
var attribution = '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>';

function init_map(inside_frame) {
    var map = L.map('map', {
        attribution: attribution,
        center: [24, 121],
        zoom: 7,
        minZoom: 6,
        maxZoom: 20,
        maxBounds: [
            [20.3, 116.6],
            [27.8, 124.3],
        ],
        fullscreenControl: !inside_frame,
    });
    return map;
}


$(function() {
    var inside_frame = (window != window.top);
    if (inside_frame) {
	$('#map').width('100%').height('100%');
    }
    var map = init_map(inside_frame);

    var timeControl = L.Control.timeControl();
    map.addControl(timeControl);

    // loading control
    var loadingControl = L.Control.loading({
        separate: true,
        position: 'topright',
    });
    map.addControl(loadingControl);

    // hash -----------------------------------------
    // TODO refactor this hash hack
    L.Hash.prototype.formatHash = function(map) {
        var hash = L.Hash.formatHash(map);
        var t1 = timeControl.getTimeStr(true).replace('-', '');
        return hash + '/' + t1;
    }
    L.Hash.prototype.parseHash = function(hash) {
        var args = hash.split('/');
	var re_time = new RegExp('([0-9]{4})([0-9]{2})?([0-9]{2})?-?([0-9]{2})?');
        if (args.length > 3) {
	    var m = args[3].match(re_time);
	    timeControl.setDate(m[1], m[2], m[3], m[4]);
        }
        return L.Hash.parseHash(args.slice(0, 3).join('/'));
    }
    var hash = new L.Hash(map);
    map.on('layeradd', hash.onMapMove, hash);
    if (!location.hash)
	timeControl.setDate(2012, 1, 1);
});
