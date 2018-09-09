import sys
import re
import json

import psycopg2
import psycopg2.errorcodes

db_user='osm_history'
db_name='osm_history'
dsn = "user='%s' dbname='%s'" % (db_user, db_name)

def find_queries(fp):
    """
    How to collect log:
        Modify /usr/local/pgsql/data/postgresql.conf
            log_destination = 'stderr'
            log_min_duration_statement = 100
        Maybe also set log_directory and log_filename
        
    """
    state = ''
    for line in fp:
        m = re.match(r'.*\bLOG:  (.+)', line)
        if m:
            if state == 'log_duration_statement':
                yield statement, duration
                state = ''


            msg = m.group(1)
            m = re.match(r'statement:(.+)', msg)
            if m:
                state = 'log_statement'
                statement = m.group(1)
                continue
            state = ''

            m = re.match(r'duration: (\d+\.\d+) ms  (execute.*?|statement)[^:]*?: (.+)', msg)
            if m:
                duration = float(m.group(1))
                statement = m.group(3)
                state = 'log_duration_statement'
                continue

            m = re.match(r'duration: (\d+\.\d+) ms', msg)
            if m:
                duration = float(m.group(1))
                yield statement, duration

        elif state in ('log_statement', 'log_duration_statement'):
            statement += line

    if state == 'log_duration_statement':
        yield statement, duration
        state = ''

def explain(cur, sql):
    # for human read
    cur.execute('EXPLAIN (ANALYZE, FORMAT TEXT) ' + sql)
    for row in cur.fetchall():
        line = row[0]
        line = re.sub(r"'\w+'::geometry", "'**********'::geometry", line)
        line = line.replace('::timestamp without time zone', '')
        print line

    # for program use
    cur.execute('EXPLAIN (ANALYZE, FORMAT JSON) ' + sql)
    rows = cur.fetchall()
    o = rows[0][0][0]
    #print json.dumps(o, indent=4)
    return o

def iter_plan(exp):
    # leaves first, root later
    if 'Plans' in exp:
        for plan in exp['Plans']:
            for p in iter_plan(plan):
                yield p

            yield plan

    if 'Plan' in exp:
        for p in iter_plan(exp['Plan']):
            yield p
        yield exp['Plan']

def is_slow_plan(plan):
    if plan.get('Actual Total Time', 0) < 10:
        return False

    if plan.get('Rows Removed by Filter', 0) > plan.get('Actual Rows') * 3:
        return True

def guess_name(plans):
    table = ''
    for p in plans:
        #print json.dumps(p, indent=4)
        if 'Relation Name' in p:
            assert table == '' or table == p['Relation Name']
            table = p['Relation Name']
    assert table

    name = ''
    for p in plans:
        alias = p.get('Alias', '')
        if not alias or alias == table:
            continue
        print 'alias', alias
        if alias not in ('', ''): # TODO
            name = alias

    return table, name

# remove extra (), replace first level "AND" with ","
def simply_cond(cond):
    nest = 0
    result = ''

    # XXX hack
    assert cond[0] == '(' and cond[-1] == ')'
    cond = cond[1:-1]

    i = 0
    while i < len(cond):
        c = cond[i]
        if c == '(':
            nest += 1
        elif c == ')':
            nest -= 1

        if nest == 0 and cond[i:].startswith(' AND '):
            result += ', '
            i += 5
            continue

        result += c
        i += 1
    return result

def extract_condition(cond):
    cond = re.sub(r'''\('[^']+'::timestamp without time zone >= valid_from\)''', '1', cond)
    cond = re.sub(r'''\('[^']+'::timestamp without time zone <= COALESCE\(valid_to, '[^']+'::timestamp without time zone\)\)''', '1', cond)
    cond = re.sub(r'''\(geom && '\w+'::geometry\)''', '1', cond)
    cond = re.sub(r'1 AND ', '', cond)
    return cond

def guess_index_name(table, cond):
    items = []
    for item in re.findall(r'(\w+)', cond):
        if item == item.upper():
            continue  # looks like SQL keyword
        if item in 'tags text char_length'.split():
            continue
        if item in items:
            continue
        items.append(item)

    print items
    if len(items) >= 2:
        name = 'idx_%s_UNKNOWN_%s_%s' % (table, items[0], items[1])
    else:
        name = 'idx_%s_UNKNOWN_%s' % (table, items[0])
    return name

def try_to_optimize(cur, query):
    print '-' * 30, 'explain original'
    exp1 = explain(cur, query)
    print
    print json.dumps(exp1, indent=4)

    t1 = exp1['Execution Time']
    if t1 < 30:
        print 'ALREADY optimized?'
        return

    plans = list(iter_plan(exp1))

    table, name = guess_name(plans)
    print

    for p in plans:
        if p.get('Node Type') in ['Bitmap Index Scan']:
            print 'ALREADY use index', p['Index Name']
    print


    for p in plans:
        if not is_slow_plan(p):
            continue

        cond = extract_condition(p['Filter'])
        cond = simply_cond(cond)


        if not name:
            idx_name = guess_index_name(table, cond)
        else:
            idx_name = 'idx_%s' % name
        sql_idx = 'CREATE INDEX %s ON %s (%s);' % (idx_name, table, cond)

        # XXX what if just name conflict?
        cur.execute(
            'SELECT relname FROM pg_class WHERE lower(relname) = lower(%s)',
            (idx_name,))
        if cur.fetchall():
            print 'index already exists:', idx_name
            return

        print '-' * 30, 'attempt to index'
        print sql_idx
        cur.execute(sql_idx)
        try:
            cur.execute('ANALYZE %s' % table)
            print

            exp2 = explain(cur, query)
            print

            t2 = exp2['Execution Time']
            print t1, '->', t2
            if t2 < t1:
                print 'GOOD'
                print sql_idx

        finally:
            cur.execute('DROP INDEX %s' % idx_name)

    return True


def is_ignore_query(query):
    if query.endswith(' LIMIT 0'):
        return True
    if not query.startswith('SELECT'):
        return True

    # XXX dirty hack, should detect duplicate index correctly
    for name in '''
    #already_indexed
    water_lines
    ferry_routes
    roads_low_zoom
    national_park_boundaries
    water_areas
    water_lines_low_zoom
    places_medium
    placenames_large
    admin_01234
    placenames_capital
    tunnels
    bridges
    sports_grounds
    buildings_lz
    glaciers_text

    #failed
    roads_casing
    roads_fill
    landcover
    roads_text_name
    '''.split():
        if re.search(r'as %s\b' % name, query):
            return True

def main():
    con = psycopg2.connect(dsn)
    cur = con.cursor()

    if len(sys.argv) > 1:
        fp = file(sys.argv[1])
    else:
        fp = sys.stdin

    for query, duration in find_queries(fp):
        if is_ignore_query(query):
            continue
        print '=' * 30
        print duration
        print query
        print

        if try_to_optimize(cur, query):
            break


if __name__ == '__main__':
    main()
