#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import os
import time
import sys
import math
import threading
import re

import cherrypy
import psycopg2
import mapnik
import pylibmc

# ----------------------------

tile_size = 256
pq_time_fmt = '%Y-%m-%d %H:%M:%S'

current_dir = os.path.dirname(os.path.abspath(__file__))

mapnik.register_fonts('/usr/share/fonts')

# ----------------------------
# hack to make cherrypy to output sub-second log
# modified from _cplogging.py
def time_hack(self):
    """Return now() in Apache Common Log Format (no timezone)."""
    now = datetime.datetime.now()
    monthnames = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                  'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    month = monthnames[now.month - 1].capitalize()
    return ('[%02d/%s/%04d:%02d:%02d:%02d.%06d]' %
            (now.day, month, now.year, now.hour, now.minute, now.second, now.microsecond))

cherrypy._cplogging.LogManager.time = time_hack

# ----------------------------

def parse_param(args):
    z, x, y, ts = 0, 0, 0, None

    if len(args) >= 3:
        z, x, y = map(int, args[:3])
        if args[3:]:
            ts = args[3]

    if not ts:
        ts = datetime.date.today().strftime('%Y%m%d')

    ts = ts.replace('-', '').replace(':', '')

    fmts = {
        4: '%Y',
        6: '%Y%m',
        8: '%Y%m%d',
        10: '%Y%m%d%H',
    }
    if len(ts) in fmts:
        dt = datetime.datetime.strptime(ts, fmts[len(ts)])
    else:
        dt = datetime.date.today()

    return z, x, y, dt

# http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)


class Options:
    def __init__(self):
        self.db_user = os.environ.get('PG_ENV_POSTGRES_USER', 'postgres')
        self.db_name = os.environ.get('PG_ENV_POSTGRES_DB', 'postgres')
        self.db_host = os.environ.get('PG_PORT_5432_TCP_ADDR', '127.0.0.1')
        self.db_port = os.environ.get('PG_PORT_5432_TCP_PORT', '5432')
        self.db_password = os.environ.get('PG_ENV_POSTGRES_PASSWORD', 'pa55w0rd')

        self.dsn = "user='%s' dbname='%s' host='%s' port='%s' password='%s'" % (
		self.db_user, self.db_name, self.db_host, self.db_port, self.db_password)
        self.dbprefix = 'hist'
        self.viewprefix = 'hist_view'
        self.date = ''
        self.style = '/web/openstreetmap-carto/style.xml'
        self.size = 256, 256

        # TODO
        self.viewcolumns = ','.join(
            """
            access addr:housename addr:housenumber addr:interpolation admin_level
            aerialway aeroway amenity area barrier bicycle brand bridge boundary
            building construction covered culvert cutting denomination disused
            embankment foot generator:source harbour highway tracktype capital
            ele historic horse intermittent junction landuse layer leisure lock
            man_made military motorcar name natural oneway operator population
            power power_source place railway ref religion route service shop
            sport surface toll tourism tower:type tunnel water waterway
            wetland width wood
            """.split())
        self.extracolumns = ''

options = None

# copied from osm-history-renderer/renderer/render.py
def create_views(con, dbprefix, viewprefix, columns, date):
    # TODO delete unused views
    cur = con.cursor()

    columselect = ""
    for column in columns:
        columselect += "tags->'%s' AS \"%s\", " % (column, column)

    cur.execute("""
        DELETE FROM geometry_columns
        WHERE f_table_catalog = '' AND f_table_schema = 'public'
            AND f_table_name IN ('%s_point', '%s_line', '%s_roads', '%s_polygon');
        """ % (viewprefix, viewprefix, viewprefix, viewprefix))

    # ----------------- point
    cur.execute(
        """
        CREATE OR REPLACE VIEW %s_point AS
            SELECT id AS osm_id, %s geom AS way
                FROM %s_point
                WHERE '%s' BETWEEN valid_from AND COALESCE(valid_to, '9999-12-31');
        """ % (viewprefix, columselect, dbprefix, date))
    cur.execute(
        """
        INSERT INTO geometry_columns
        (f_table_catalog, f_table_schema, f_table_name, f_geometry_column, coord_dimension, srid, type)
        VALUES ('', 'public', '%s_point', 'way', 2, 900913, 'POINT');""" % (viewprefix))

    # ----------------- line
    cur.execute(
        """
        CREATE OR REPLACE VIEW %s_line AS
        SELECT id AS osm_id, %s z_order, geom AS way
            FROM %s_line
            WHERE '%s' BETWEEN valid_from AND COALESCE(valid_to, '9999-12-31');
        """ % (viewprefix, columselect, dbprefix, date))
    cur.execute(
        """
        INSERT INTO geometry_columns
        (f_table_catalog, f_table_schema, f_table_name, f_geometry_column, coord_dimension, srid, type)
        VALUES ('', 'public', '%s_line', 'way', 2, 900913, 'LINESTRING');""" % (viewprefix))

    # ----------------- roads
    cur.execute(
        """
        CREATE OR REPLACE VIEW %s_roads AS
        SELECT id AS osm_id, %s z_order, geom AS way
            FROM %s_line
            WHERE '%s' BETWEEN valid_from AND COALESCE(valid_to, '9999-12-31');
        """ % (viewprefix, columselect, dbprefix, date))
    cur.execute(
        """
        INSERT INTO geometry_columns
        (f_table_catalog, f_table_schema, f_table_name, f_geometry_column, coord_dimension, srid, type)
        VALUES ('', 'public', '%s_roads', 'way', 2, 900913, 'LINESTRING');""" % (viewprefix))

    # ----------------- polygon
    cur.execute(
        """
        CREATE OR REPLACE VIEW %s_polygon AS
        SELECT id AS osm_id, %s z_order, area AS way_area, geom AS way
            FROM %s_polygon
            WHERE '%s' BETWEEN valid_from AND COALESCE(valid_to, '9999-12-31');
        """ % (viewprefix, columselect, dbprefix, date))
    cur.execute(
        """
        INSERT INTO geometry_columns
        (f_table_catalog, f_table_schema, f_table_name, f_geometry_column, coord_dimension, srid, type)
        VALUES ('', 'public', '%s_polygon', 'way', 2, 900913, 'POLYGON');""" % (viewprefix))

    con.commit()
    cur.close()

class Requests:
    def __init__(self):
        self.lock = threading.Lock()
        self.requests = []

    def add(self, z, x, y):
        with self.lock:
            self.requests.append((z, x, y))

    @staticmethod
    def with_in(z, x, y, w, h, o):
        return o[0] == z and x <= o[1] < x + w and y <= o[2] < y + h

    def collect(self, z, x, y):
        "return nearby requests"
        bx, by = x, y
        bw, bh = 1, 1

        # TODO try other strategy
        bx = x / 3 * 3
        by = y / 3 * 3
        bw, bh = 3, 3

        with self.lock:

            todo = []
            remain = []
            for o in self.requests:
                if self.with_in(z, bx, by, bw, bh, o):
                    todo.append(o)
                else:
                    remain.append(o)

            print 'requests', len(self.requests), self.requests
            print (bx, by, bw, bh), 'covers', len(todo), todo

            self.requests = remain

        return bx, by, bw, bh

class Renderer:
    def __init__(self, dt):
        self.lock = threading.Lock()
        self.dt = dt
        self.inited = False
        self.requests = Requests()

    def init(self):
        if self.inited:
            return False
        cherrypy.log('init db %s' % self.dt)
        self.init_db(self.dt)
        cherrypy.log('init mapnik')
        self.init_mapnik()
        cherrypy.log('init done')
        self.inited = True
        return True

    def init_db(self, dt):
        con = psycopg2.connect(options.dsn)

        self.viewprefix = options.viewprefix + dt.strftime('_%Y%m%d_%H%M')
        pq_time = dt.strftime(pq_time_fmt)

        columns = options.viewcolumns.split(',')
        if options.extracolumns:
            columns += options.extracolumns.split(',')
        # takes 300ms
        create_views(con, options.dbprefix, self.viewprefix, columns, pq_time)

    def init_mapnik(self):
        style = file(options.style).read()
        style = style.replace('"dbname": "gis"', '"dbname": "%s"' % options.db_name)
        style = style.replace('"dbname"><![CDATA[gis]]>', '"dbname"><![CDATA[%s]]>' % options.db_name)
        for type in ('point', 'line', 'roads', 'polygon'):
            style = style.replace('planet_osm_%s' % type,
                                  self.viewprefix + '_' + type)


        m = mapnik.Map(tile_size, tile_size)
        m.buffer_size = 128
        # mapnik takes 700ms in db init
	strict = False
        mapnik.load_map_from_string(m, style, strict, '/web/openstreetmap-carto')

        m.resize(tile_size, tile_size)

        self.m = m


    def render_one_tile(self, zoom, x, y):

        bbox = [0, 0, 0, 0]
        bbox[3], bbox[0] = num2deg(x, y, zoom)
        bbox[1], bbox[2] = num2deg(x + 1, y + 1, zoom)
        bbox = mapnik.Box2d(*bbox)

        prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")
        e = mapnik.forward_(bbox, prj)
        self.m.zoom_to_box(e)

        s = mapnik.Image(tile_size, tile_size)
        mapnik.render(self.m, s)

        view = s.view(0, 0, tile_size, tile_size)
        return view.tostring('png')

    def render_tiles(self, zoom, bx, by, bw, bh):
        cherrypy.log('RENDER z=%d (%d,%d) (%d,%d)' % (zoom, bx, by, bw, bh))
        bbox = [0, 0, 0, 0]
        bbox[3], bbox[0] = num2deg(bx, by, zoom)
        bbox[1], bbox[2] = num2deg(bx + bw, by + bh, zoom)
        bbox = mapnik.Box2d(*bbox)

        self.m.resize(tile_size * bw, tile_size * bh)

        prj = mapnik.Projection("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over")
        e = mapnik.forward_(bbox, prj)
        self.m.zoom_to_box(e)

        s = mapnik.Image(tile_size * bw, tile_size * bh)
        mapnik.render(self.m, s)

        for x in range(bx, bx + bw):
            for y in range(by, by + bh):
                ox = (x - bx) * tile_size
                oy = (y - by) * tile_size
                view = s.view(ox, oy, tile_size, tile_size)
                yield (x, y), view.tostring('png')
        cherrypy.log('RENDER end')


class Cache:
    def __init__(self):
        self.lock = threading.Lock()
        host = 'memcache'
        self.mc = pylibmc.Client([host], binary=True,
                                 behaviors={"tcp_nodelay": True,
                                            #'hash': 'murmur',
                                            })

    @staticmethod
    def cache_key(z, x, y, dt):
        return 'history/%d,%d,%d,%s' % (z, x, y, dt)

    def get(self, key):
        with self.lock:
            return self.mc.get(key)

    def put(self, key, data, time):
        with self.lock:
            self.mc.set(key, data, time=time)

    def get_tile(self, z, x, y, dt):
        key = self.cache_key(z, x, y, dt)
        return self.get(key)

    def put_tile(self, z, x, y, dt, data):
        key = self.cache_key(z, x, y, dt)
        self.put(key, data, 86400)


cache = Cache()


class RendererPool:
    def __init__(self):
        self.lock = threading.Lock()
        self.pool = []

    def get(self, dt):
        with self.lock:
            found = None
            for r in self.pool:
                if r.dt == dt:
                    found = r
                    break

            if found:
                self.pool.remove(found)
                self.pool.append(found)
                return found

            r = Renderer(dt)
            self.pool.append(r)
            if len(self.pool) > 100:
                self.pool = self.pool[-100:]  # LRU
            return r


def query_last_modified_time(dt):
    pq_time = dt.strftime(pq_time_fmt)

    # do we still need this? it's already indexed and fast
    key = 'last_modified_time/%s' % pq_time
    if cache.get(key):
        return cache.get(key)

    last_modified_time = datetime.datetime(2000, 1, 1)

    con = psycopg2.connect(options.dsn)
    cur = con.cursor()
    for type in ('point', 'line', 'polygon'):
        for field in ('valid_to', 'valid_from'):
            sql = """
            SELECT %s
            FROM hist_%s
            WHERE '%s' >= %s ORDER BY %s DESC LIMIT 1
            """ % (field, type, pq_time, field, field)
            #cherrypy.log(sql)
            cur.execute(sql)
            rows = cur.fetchall()
            if rows:
                t = rows[0][0]
                if t > last_modified_time:
                    last_modified_time = t

    cache.put(key, last_modified_time, 86400)

    return last_modified_time

class TileServer:
    def __init__(self):
        self.pool = RendererPool()
        self.db_lock = threading.Lock()

    default = cherrypy.tools.staticdir.handler(
        section='', dir=os.path.join(current_dir, 'static'),
        index='index.html'
    )

    @cherrypy.expose
    def history_tile(self, *args, **argd):
        z, x, y, dt = parse_param(args)
        cherrypy.log('request %d,%d,%d %s ' % (z, x, y, dt))
        # TODO
        #if dt.strftime('%Y%m%d') > data_timestamp.data_date:
        #    raise cherrypy.HTTPError('404 Not Found')

        # last modified time
        # Note, this may miss 1 second of data.
        with self.db_lock:
            last_modified_time = query_last_modified_time(dt)
        cherrypy.log('request %d,%d,%d %s => %s' % (z, x, y, dt, last_modified_time))
        dt = last_modified_time

        cherrypy.response.headers['Content-Type'] = 'image/png'

        result = cache.get_tile(z, x, y, dt)
        if result:
            return result

        render = self.pool.get(dt)
        render.requests.add(z, x, y)
        with render.lock:
            # check cache again
            result = cache.get_tile(z, x, y, dt)
            if result:
                return result

            with self.db_lock:
                if not render.init():
                    time.sleep(0.1)  # wait for nearby requests arrival

            bx, by, bw, bh = render.requests.collect(z, x, y)
            result = None
            with self.db_lock:
                for (qx, qy), png in render.render_tiles(z, bx, by, bw, bh):
                    cache.put_tile(z, qx, qy, dt, png)
                    if qx == x and qy == y:
                        result = png

            assert result

        return result


def server():
    cherrypy.config.update({
        #'server.socket_host': '192.168.0.254',
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8080,
        #'server.thread_pool': 1,
    })

    cherrypy.quickstart(TileServer())

def command_line():

    z, x, y, dt = parse_param(sys.argv[2:])
    renderer = Renderer(dt)
    print >> sys.stderr, z, x, y, dt
    print >> sys.stderr, 'init db'
    renderer.init_db(dt)
    print >> sys.stderr, 'init mapnik'
    renderer.init_mapnik()


    print >> sys.stderr, 'render'
    result = renderer.render_one_tile(z, x, y)
    sys.stdout.write(result)

def main():
    global options
    if sys.argv[1:] and sys.argv[1] == 'tile':
        options = Options()
        command_line()
    else:
        options = Options()
        server()

if __name__ == '__main__':
    main()
