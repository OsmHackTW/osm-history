
var attribution = '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>';

function init_map(id) {
    var map = L.map(id, {
	attribution: attribution,
	center: new L.LatLng(24, 121),
	zoom: 8,
	minZoom: 5,
	maxZoom: 20,
    });
    return map;
}


$(function() {
    var map1 = init_map('map1');
    var map2 = init_map('map2');
    var maps = [map1, map2];
    var timeControl = [null, null];

    for (var i = 0; i < maps.length; i++) {
	var map = maps[i];


	timeControl[i] = L.Control.timeControl();
	map.addControl(timeControl[i]);

	// loading control
	var loadingControl = L.Control.loading({
		separate: true,
		position: 'topright',
	});
	map.addControl(loadingControl);


	timeControl[i].setDate(2008 + i*2, 1, 1);
    }
    map1.sync(map2);
    map2.sync(map1);

    // hash -----------------------------------------
    // TODO refactor this hash hack
    L.Hash.prototype.formatHash = function(map) {
        var hash = L.Hash.formatHash(map);
        var t1 = timeControl[0].getTimeStr(true).replace('-', '');
	var t2 = timeControl[1].getTimeStr(true).replace('-', '');
        return hash + '/' + t1 + '/' + t2;
    }
    L.Hash.prototype.parseHash = function(hash) {
        var args = hash.split('/');
	var re_time = new RegExp('([0-9]{4})([0-9]{2})?([0-9]{2})?-?([0-9]{2})?');
        if (args.length > 3) {
	    var m = args[3].match(re_time);
	    timeControl[0].setDate(m[1], m[2], m[3], m[4]);
	    var m = args[4].match(re_time);
	    timeControl[1].setDate(m[1], m[2], m[3], m[4]);
        }
        return L.Hash.parseHash(args.slice(0, 3).join('/'));
    }
    var hash = new L.Hash(map1);
    map1.on('layeradd', hash.onMapMove, hash);
    map2.on('layeradd', hash.onMapMove, hash);
    if (!location.hash)
	timeControl.setDate(2008, 1, 1);
});
