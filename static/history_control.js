
var attribution = '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>';

function create_history_layer(date, max_zoom) {
    if (!max_zoom) max_zoom = 20;
    if (date == 'today') {
        return L.tileLayer(
            'http://c.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: attribution,
            maxZoom: max_zoom,
        });
    }

    return L.tileLayer(
        'history_tile/{z}/{x}/{y}/' + date, {
        attribution: attribution,
        maxZoom: max_zoom,
        updateWhenIdle: true,  // because my tile server is too slow
        unloadInvisibleTiles: true,
    });
}

L.Control.TimeControl = L.Control.extend({
    options: {
        position: 'topright',
        min_year: 2007,
    },
    initialize: function(options) {
        L.Util.setOptions(this, options);
    },
    onAdd: function(map) {
        var self = this;
        this.options.map = map;

        var spin_y = $('<input class="leaflet-timespin-year" maxlength=4 size=4>');
        var spin_m = $('<input class="leaflet-timespin-month" maxlength=2 size=2 value=1>');
        var spin_d = $('<input class="leaflet-timespin-day" maxlength=2 size=2 value=1>');
        var spin_h = $('<input class="leaflet-timespin-hour" maxlength=2 size=2 value=0>');
        var container = L.DomUtil.create('div');
        L.DomEvent.on(container, 'dblclick', L.DomEvent.stopPropagation);
        $(container).append('<div class="leaflet-timespin">').append(
            spin_y, spin_m, spin_d, spin_h
        );

        spin_y.spinner({
            min: this.options.min_year,
            max: new Date().getYear() + 1900,
            change: function(event, ui) {
            },
            spin: function(event, ui) {
                self.setDate(ui.value, 1, 1, 0);
                return false;
            },
        }).spinner('value', new Date().getYear() + 1900);
        spin_m.spinner({
            min: 1-1,
            max: 12+1,
            spin: function(event, ui) {
                self.setDate(spin_y.spinner('value'), ui.value, 1, 0);
                return false;
            },
        });
        spin_d.spinner({
            min: 1-1,
            max: 31+1,
            spin: function(event, ui) {
                self.setDate(spin_y.spinner('value'), spin_m.spinner('value'), ui.value, 0);
                return false;
            },
        });
        spin_h.spinner({
            min: 0-1,
            max: 23+1,
            spin: function(event, ui) {
                self.setDate(spin_y.spinner('value'), spin_m.spinner('value'), spin_d.spinner('value'), ui.value);
                return false;
            },
        });
        function changed(event, ui) {
            self.setDate(spin_y.spinner('value'), spin_m.spinner('value'), spin_d.spinner('value'), spin_h.spinner('value'));
        }
        spin_y.on('spinchange', changed);
        spin_m.on('spinchange', changed);
        spin_d.on('spinchange', changed);
        spin_h.on('spinchange', changed);

        return container;
    },
    onRemove: function(map) {
        $('.leaflet-timespin').remove();
    },
    setDate: function(y, m, d, h) {
        var self = this;
	if (m == null) m = 1;
	if (d == null) d = 1;
        if (h == null) h = 0;
        //console.log(y + ',' + m + ',' + d + ',' + h);

        var container = this.options.map.getContainer();
        var spin_y = $(container).find('.leaflet-timespin-year');
        var spin_m = $(container).find('.leaflet-timespin-month');
        var spin_d = $(container).find('.leaflet-timespin-day');
        var spin_h = $(container).find('.leaflet-timespin-hour');
        // JavaScript spec says it's ok if the values is out of range.
        var v = new Date(y, m - 1, d, h);
        if (v.getFullYear() < this.options.min_year)
            v.setYear(this.options.min_year);
        //console.log(v);
	this._time = v;
        if (spin_y.spinner('value') != v.getFullYear())
            spin_y.spinner('value', v.getFullYear());
        if (spin_m.spinner('value') != v.getMonth() + 1)
            spin_m.spinner('value', v.getMonth() + 1);
        if (spin_d.spinner('value') != v.getDate())
            spin_d.spinner('value', v.getDate());
        if (spin_h.spinner('value') != v.getHours())
            spin_h.spinner('value', v.getHours());
        if (this.timeoutId)
            clearTimeout(this.timeoutId);
        this.timeoutId = setTimeout(function(){self._timeChanged()}, 1000);
    },
    getTimeStr: function(simplify) {
        function pad(v, len) {
            var s = "" + v;
            while (s.length < len)
                s = "0" + s;
            return s;
        }
	var t = this._time;
        var v = pad(t.getFullYear(), 4) + pad(t.getMonth() + 1, 2) + pad(t.getDate(), 2) + '-' + pad(t.getHours(), 2);
	if (!simplify)
	    return v;

	if (t.getHours() == 0) {
	    v = v.slice(0, 8);
	    if (t.getDate() == 1) {
		v = v.slice(0, 6);
		if (t.getMonth() == 0) {
		    v = v.slice(0, 4);
		}
	    }
	}
	return v;
    },
    _timeChanged: function() {
        var self = this;
        //console.log('time_changed');
        var container = this.options.map.getContainer();

	if (this._layer_time == this._time)
	    return;
	this._layer_time = this._time;

	var v = this.getTimeStr();
        console.log(v);

        var layer = create_history_layer(v);
        // why sometimes no 'load' event?
        layer.on('loading', function () {
            layer.loadstart = new Date();
        });
        layer.on('load', function () {
            var now = new Date();
            var t = now - layer.loadstart;
            console.log(t + 'ms');
            var showtime = $(container).find('.show-loadtime');
            if (showtime)
                showtime.text();
        });
        this._switch_layer(layer);
    },
    _switch_layer: function(newlayer) {
        // remove old layers
        var map = this.options.map;
        for (var id in map._layers) {
            var layer = map._layers[id];
            map.removeLayer(layer);
        }

        map.addLayer(newlayer);
    },
})

L.Control.timeControl = function (options) {
    return new L.Control.TimeControl(options);
}
