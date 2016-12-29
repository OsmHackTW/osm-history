-- How to find them:
-- 1. Enable postgresql logging of slow query
-- 2. 'explain' the queries.
--    Usually, they are low zoom level and not efficient to use geom index.
--    Find conditions almost false.
-- 3. Create index by taking conditions beside geom and valid time.
--    Replace first level "AND" as ","
-- 4. Verify the index really make things faster

CREATE INDEX point_valid_to_index ON hist_point (valid_to);
CREATE INDEX point_valid_from_index ON hist_point (valid_from);
CREATE INDEX line_valid_to_index ON hist_line (valid_to);
CREATE INDEX line_valid_from_index ON hist_line (valid_from);
CREATE INDEX polygon_valid_to_index ON hist_polygon (valid_to);
CREATE INDEX polygon_valid_from_index ON hist_polygon (valid_from);

CREATE INDEX placenames_capital_idx ON hist_point (((tags -> 'place'::text) = ANY ('{city,town}'::text[])), ((tags -> 'capital'::text) = 'yes'::text));
CREATE INDEX admin_01234_idx ON hist_line (((tags -> 'boundary'::text) = 'administrative'::text), ((tags -> 'admin_level'::text) = ANY ('{0,1,2,3,4}'::text[])));
CREATE INDEX placenames_large_idx ON hist_point (((tags -> 'place'::text) = ANY ('{country,state}'::text[])));
CREATE INDEX placenames_medium_idx ON hist_point (((tags -> 'place'::text) = ANY ('{city,town}'::text[])), (((tags -> 'capital'::text) IS NULL) OR ((tags -> 'capital'::text) <> 'yes'::text)));
CREATE INDEX water_lines_low_zoom_idx ON hist_line (((tags -> 'waterway'::text) = 'river'::text));
CREATE INDEX water_areas_idx ON hist_polygon ((((tags -> 'waterway'::text) = ANY ('{dock,mill_pond,riverbank,canal}'::text[])) OR ((tags -> 'landuse'::text) = ANY ('{reservoir,water,basin}'::text[])) OR ((tags -> 'natural'::text) = ANY ('{lake,water,land,glacier,mud}'::text[]))));
CREATE INDEX national_park_boundaries_idx ON hist_polygon (((tags -> 'boundary'::text) = 'national_park'::text));
CREATE INDEX roads_low_zoom_idx ON hist_line ((((tags -> 'highway'::text) = ANY ('{motorway,motorway_link,trunk,trunk_link,primary,primary_link,secondary,secondary_link}'::text[])) OR (((tags -> 'railway'::text) IS NOT NULL) AND ((tags -> 'railway'::text) <> 'preserved'::text) AND (((tags -> 'service'::text) IS NULL) OR ((tags -> 'service'::text) <> ALL ('{spur,siding,yard}'::text[]))))));
CREATE INDEX ferry_routes_idx ON hist_line (((tags -> 'route'::text) = 'ferry'::text));
CREATE INDEX water_lines_idx ON hist_line ((((tags -> 'bridge'::text) IS NULL) OR ((tags -> 'bridge'::text) <> ALL ('{yes,true,1,aqueduct}'::text[]))), ((tags -> 'waterway'::text) = ANY ('{weir,river,canal,derelict_canal,stream,drain,ditch,wadi}'::text[])));
CREATE INDEX idx_hist_line_man_made_pier ON hist_line (((tags -> 'man_made'::text) = ANY ('{pier,breakwater,groyne}'::text[])));
CREATE INDEX idx_tunnels ON hist_line (((tags -> 'tunnel'::text) = 'yes'::text), ((tags -> 'highway'::text) = ANY ('{motorway,motorway_link,trunk,trunk_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,residential,unclassified,bridleway,footway,cycleway,path,track}'::text[])));
CREATE INDEX idx_bridges ON hist_line (((tags -> 'bridge'::text) = ANY ('{yes,true,1,viaduct}'::text[])), (((tags -> 'layer'::text) IS NULL) OR ((tags -> 'layer'::text) = ANY ('{0,1,2,3,4,5}'::text[]))), (((tags -> 'highway'::text) IS NOT NULL) OR ((tags -> 'aeroway'::text) = ANY ('{runway,taxiway}'::text[])) OR ((tags -> 'railway'::text) = ANY ('{light_rail,subway,narrow_gauge,rail,spur,siding,disused,abandoned,construction}'::text[]))));

CREATE INDEX idx_hist_point_place_suburb ON hist_point (((tags -> 'place'::text) = ANY ('{suburb,village,hamlet,neighbourhood,locality,isolated_dwelling,farm}'::text[])));
CREATE INDEX idx_hist_point_railway_station ON hist_point ((((tags -> 'railway'::text) = ANY ('{station,halt,tram_stop,subway_entrance}'::text[])) OR ((tags -> 'aerialway'::text) = 'station'::text)));
CREATE INDEX idx_hist_point_aeroway_aerodrome ON hist_point ((((tags -> 'aeroway'::text) = ANY ('{aerodrome,helipad}'::text[])) OR ((tags -> 'barrier'::text) = ANY ('{bollard,gate,lift_gate,block}'::text[])) OR ((tags -> 'highway'::text) = ANY ('{mini_roundabout,gate}'::text[])) OR ((tags -> 'man_made'::text) = ANY ('{lighthouse,power_wind,windmill,mast}'::text[])) OR (((tags -> 'power'::text) = 'generator'::text) AND (((tags -> 'generator:source'::text) = 'wind'::text) OR ((tags -> 'power_source'::text) = 'wind'::text))) OR ((tags -> 'natural'::text) = ANY ('{peak,volcano,spring,tree,cave_entrance}'::text[])) OR ((tags -> 'railway'::text) = 'level_crossing'::text)));
CREATE INDEX idx_hist_line_ref_highway ON hist_line (((tags -> 'ref'::text) IS NOT NULL), ((tags -> 'highway'::text) = ANY ('{motorway,trunk,primary,secondary}'::text[])), (char_length((tags -> 'ref'::text)) >= 1), (char_length((tags -> 'ref'::text)) <= 8));
CREATE INDEX idx_hist_point_highway_motorway_junction ON hist_point (((tags -> 'highway'::text) = 'motorway_junction'::text));
CREATE INDEX idx_hist_point_amenity_shop ON hist_point ((((tags -> 'amenity'::text) IS NOT NULL) OR ((tags -> 'shop'::text) = ANY ('{supermarket,bakery,clothes,fashion,convenience,doityourself,hairdresser,department_store,butcher,car,car_repair,bicycle,florist}'::text[])) OR ((tags -> 'leisure'::text) IS NOT NULL) OR ((tags -> 'landuse'::text) IS NOT NULL) OR ((tags -> 'tourism'::text) IS NOT NULL) OR ((tags -> 'natural'::text) IS NOT NULL) OR ((tags -> 'man_made'::text) = ANY ('{lighthouse,windmill}'::text[])) OR ((tags -> 'place'::text) = 'island'::text) OR ((tags -> 'military'::text) = 'danger_area'::text) OR ((tags -> 'aeroway'::text) = 'gate'::text) OR ((tags -> 'waterway'::text) = 'lock'::text) OR ((tags -> 'historic'::text) = ANY ('{memorial,archaeological_site}'::text[]))));
CREATE INDEX idx_sports_grounds ON hist_polygon (((tags -> 'leisure'::text) = ANY ('{sports_centre,stadium,pitch,track}'::text[])));
CREATE INDEX idx_hist_polygon_building_landuse ON hist_polygon (((tags -> 'building'::text) IS NULL), (((tags -> 'landuse'::text) = 'military'::text) OR ((tags -> 'leisure'::text) = 'nature_reserve'::text)));
CREATE INDEX idx_hist_line_waterway_stream ON hist_line (((tags -> 'waterway'::text) = ANY ('{stream,drain,ditch}'::text[])), (((tags -> 'tunnel'::text) IS NULL) OR ((tags -> 'tunnel'::text) <> 'yes'::text)));
CREATE INDEX idx_hist_polygon_aeroway_aerodrome ON hist_polygon ((((tags -> 'aeroway'::text) = ANY ('{aerodrome,helipad}'::text[])) OR ((tags -> 'barrier'::text) = ANY ('{bollard,gate,lift_gate,block}'::text[])) OR ((tags -> 'highway'::text) = ANY ('{mini_roundabout,gate}'::text[])) OR ((tags -> 'man_made'::text) = ANY ('{lighthouse,power_wind,windmill,mast}'::text[])) OR (((tags -> 'power'::text) = 'generator'::text) AND (((tags -> 'generator:source'::text) = 'wind'::text) OR ((tags -> 'power_source'::text) = 'wind'::text))) OR ((tags -> 'natural'::text) = ANY ('{peak,volcano,spring,tree}'::text[])) OR ((tags -> 'railway'::text) = 'level_crossing'::text)));
CREATE INDEX idx_buildings_lz ON hist_polygon ((((tags -> 'railway'::text) = 'station'::text) OR ((tags -> 'building'::text) = ANY ('{station,supermarket}'::text[])) OR ((tags -> 'amenity'::text) = 'place_of_worship'::text)));
CREATE INDEX idx_glaciers_text ON hist_polygon (((tags -> 'building'::text) IS NULL), ((tags -> 'natural'::text) = 'glacier'::text));
CREATE INDEX idx_hist_line_aerialway ON hist_line (((tags -> 'aerialway'::text) IS NOT NULL));
CREATE INDEX idx_hist_line_natural_cliff ON hist_line ((((tags -> 'natural'::text) = 'cliff'::text) OR ((tags -> 'man_made'::text) = 'embankment'::text)));
CREATE INDEX idx_hist_line_highway_bus_guideway ON hist_line (((tags -> 'highway'::text) = 'bus_guideway'::text), (((tags -> 'tunnel'::text) IS NULL) OR ((tags -> 'tunnel'::text) <> 'yes'::text)));
CREATE INDEX idx_hist_line_waterway_dam ON hist_line (((tags -> 'waterway'::text) = 'dam'::text));
CREATE INDEX idx_hist_line_boundary_administrative ON hist_line (((tags -> 'boundary'::text) = 'administrative'::text), ((tags -> 'admin_level'::text) = ANY ('{5,6,7,8}'::text[])));
CREATE INDEX idx_hist_line_railway_tram ON hist_line (((tags -> 'railway'::text) = 'tram'::text), (((tags -> 'tunnel'::text) IS NULL) OR ((tags -> 'tunnel'::text) <> 'yes'::text)));
CREATE INDEX idx_hist_point_power_tower ON hist_point (((tags -> 'power'::text) = 'tower'::text));
CREATE INDEX idx_buildings ON hist_polygon (((((tags -> 'building'::text) IS NOT NULL) AND ((tags -> 'building'::text) <> ALL ('{no,station,supermarket,planned}'::text[])) AND (((tags -> 'railway'::text) IS NULL) OR ((tags -> 'railway'::text) <> 'station'::text)) AND (((tags -> 'amenity'::text) IS NULL) OR ((tags -> 'amenity'::text) <> 'place_of_worship'::text))) OR ((tags -> 'aeroway'::text) = 'terminal'::text)));
CREATE INDEX idx_water_lines_text ON hist_line (((tags -> 'waterway'::text) = ANY ('{weir,river,canal,derelict_canal,stream,drain,ditch,wadi}'::text[])));
CREATE INDEX idx_hist_point_place_city ON hist_point (((tags -> 'place'::text) = ANY ('{city,town}'::text[])), (((tags -> 'capital'::text) IS NULL) OR ((tags -> 'capital'::text) <> 'yes'::text)));
ANALYZE;
