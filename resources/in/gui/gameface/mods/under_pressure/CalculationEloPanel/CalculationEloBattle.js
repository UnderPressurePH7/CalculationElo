(function () {
    'use strict';

    var root = document.getElementById('elo-root');
    var titleEl = document.getElementById('elo-title');
    var namesEl = document.getElementById('elo-names');
    var alliesNameEl = document.getElementById('elo-allies-name');
    var enemiesNameEl = document.getElementById('elo-enemies-name');
    var ratingsEl = document.getElementById('elo-ratings');
    var alliesRatingEl = document.getElementById('elo-allies-rating');
    var enemiesRatingEl = document.getElementById('elo-enemies-rating');
    var changesEl = document.getElementById('elo-changes');
    var gainEl = document.getElementById('elo-gain');
    var lossEl = document.getElementById('elo-loss');
    var statsEl = document.getElementById('elo-stats');
    var battlesEl = document.getElementById('elo-battles');
    var winrateEl = document.getElementById('elo-winrate');
    var statsSeparatorEl = document.getElementById('elo-stats-separator');

    var lastPayload = null;
    var lastSize = null;
    var payload = {};
    var debugSent = false;

    function debug(message) {
        try {
            if (window.model && typeof window.model.onDebug === 'function') {
                window.model.onDebug({ message: String(message) });
            }
        } catch (e) {}
    }

    function describeEl(name, el) {
        var text = el.textContent;
        var info = name + '="' + text + '" ' + el.offsetWidth + 'x' + el.offsetHeight;
        try {
            var cs = window.getComputedStyle(el);
            info += ' color=' + cs.color + ' font=' + cs.fontFamily + '/' + cs.fontWeight + '/' + cs.fontSize + ' display=' + cs.display;
        } catch (e) {
            info += ' (no computed style)';
        }
        return info;
    }

    function sendDebugDump() {
        debug(describeEl('alliesName', alliesNameEl));
        debug(describeEl('alliesRating', alliesRatingEl));
        debug(describeEl('gain', gainEl));
        debug(describeEl('winrate', winrateEl));
        debug(describeEl('separator', statsSeparatorEl));
        debug(describeEl('battles', battlesEl));
        debug(describeEl('root', root));
    }

    function toInt(value, fallback) {
        var parsed = parseInt(value, 10);
        return isNaN(parsed) ? fallback : parsed;
    }

    function toNumber(value, fallback) {
        var parsed = parseFloat(value);
        return isNaN(parsed) ? fallback : parsed;
    }

    function px(value) {
        return value + 'px';
    }

    function color(value, fallback) {
        value = value || fallback || 'FFFFFF';
        return '#' + String(value).replace('#', '');
    }

    function truncateName(value) {
        value = value ? String(value) : ' ';
        if (value === 'Unknown' || value === ' ') {
            return ' ';
        }
        value = value.toUpperCase();
        return value.length > 6 ? value.substr(0, 6) : value;
    }

    function winrateColor(value) {
        if (value >= 75) return '#D042F3';
        if (value >= 65) return '#02C9B3';
        if (value >= 58) return '#60FF00';
        if (value >= 50) return '#F8F400';
        if (value >= 40) return '#FE7903';
        if (value >= 30) return '#FE0E00';
        return '#FFFFFF';
    }

    function battlesColor(value) {
        if (value >= 800) return '#D042F3';
        if (value >= 500) return '#02C9B3';
        if (value >= 400) return '#60FF00';
        if (value >= 350) return '#F8F400';
        return '#FFFFFF';
    }

    function formatWinrate(value) {
        return Math.round(value) + '%';
    }

    function setVisible(el, visible) {
        el.style.display = visible ? '' : 'none';
    }

    function setRowHeight(el, value) {
        el.style.height = px(value);
    }

    function applyLayout(scale, size) {
        var shadowSize = Math.max(1, Math.round(scale));
        root.style.width = px(size.w);
        root.style.padding = px(Math.round(5 * scale));
        root.style.borderRadius = px(Math.round(6 * scale));
        root.style.textShadow = px(shadowSize) + ' ' + px(shadowSize) + ' ' + px(Math.max(2, Math.round(2 * scale))) + ' rgba(0, 0, 0, 0.7)';
        titleEl.style.fontSize = px(Math.round(14 * scale));
        namesEl.style.fontSize = px(Math.round(17 * scale));
        ratingsEl.style.fontSize = px(Math.round(22 * scale));
        changesEl.style.fontSize = px(Math.round(14 * scale));
        statsEl.style.fontSize = px(Math.round(14 * scale));
        setRowHeight(titleEl, Math.round(22 * scale));
        setRowHeight(namesEl, Math.round(23 * scale));
        setRowHeight(ratingsEl, Math.round(26 * scale));
        setRowHeight(changesEl, Math.round(18 * scale));
        setRowHeight(statsEl, Math.round(18 * scale));
        statsSeparatorEl.style.paddingLeft = px(Math.round(4 * scale));
        statsSeparatorEl.style.paddingRight = px(Math.round(4 * scale));
    }

    function readPayload() {
        var raw = window.model && window.model.payload ? String(window.model.payload) : '';
        if (raw === lastPayload) {
            return;
        }
        lastPayload = raw;
        try {
            payload = JSON.parse(raw || '{}');
        } catch (e) {
            payload = {};
        }
    }

    function render() {
        readPayload();
        var cfg = payload.config || {};
        var state = payload.state || {};
        var size = payload.size || {};
        var scale = Number(payload.scale) || 1;
        var width = toInt(size.w, 140);
        var height = toInt(size.h, 110);
        var sizeKey = width + 'x' + height;

        root.style.display = payload.visible === false ? 'none' : 'block';
        applyLayout(scale, { w: width, h: height });

        titleEl.textContent = cfg.headerText || 'ELO Calculator';
        titleEl.style.color = color(cfg.headerColor, 'FFFFFF');
        setVisible(titleEl, !!cfg.showTitle);

        setVisible(namesEl, cfg.showTeamNames !== false);
        alliesNameEl.textContent = truncateName(state.allies_name);
        enemiesNameEl.textContent = truncateName(state.enemies_name);
        alliesNameEl.style.color = color(cfg.alliesNamesColor, '4F8627');
        enemiesNameEl.style.color = color(cfg.enemiesNamesColor, '9A0101');

        var alliesRating = toInt(state.allies_rating, 0);
        var enemiesRating = toInt(state.enemies_rating, 0);
        alliesRatingEl.textContent = alliesRating > 0 ? String(alliesRating) : ' ';
        enemiesRatingEl.textContent = enemiesRating > 0 ? String(enemiesRating) : ' ';
        alliesRatingEl.style.color = color(cfg.alliesRatingColor, '4F8627');
        enemiesRatingEl.style.color = color(cfg.enemiesRatingColor, '9A0101');

        setVisible(changesEl, cfg.showEloChanges !== false);
        var gain = toInt(state.elo_plus, 0);
        var loss = toInt(state.elo_minus, 0);
        gainEl.textContent = gain > 0 ? '+' + gain : '';
        lossEl.textContent = loss < 0 ? String(loss) : '';
        gainEl.style.color = color(cfg.eloGainColor, '00FF00');
        lossEl.style.color = color(cfg.eloLossColor, 'FF0000');

        setVisible(statsEl, cfg.showWinrateAndBattles !== false);
        var battles = toInt(state.battles_count, 0);
        var winrate = toNumber(state.wins_percent, 0);
        var hasStats = battles > 0 || winrate > 0;
        winrateEl.textContent = hasStats ? formatWinrate(winrate) : '';
        statsSeparatorEl.textContent = hasStats ? '|' : '';
        battlesEl.textContent = hasStats ? String(battles) : '';
        winrateEl.style.color = winrateColor(winrate);
        battlesEl.style.color = battlesColor(battles);

        if (sizeKey !== lastSize && window.viewEnv && viewEnv.resizeViewPx) {
            lastSize = sizeKey;
            viewEnv.resizeViewPx(width, height);
        }

        if (!debugSent && toInt(state.allies_rating, 0) > 0) {
            debugSent = true;
            window.setTimeout(sendDebugDump, 500);
        }
    }

    function poll() {
        var raw = window.model && window.model.payload ? String(window.model.payload) : '';
        if (raw !== lastPayload) {
            render();
        }
    }

    function initialize() {
        render();
        if (window.engine) {
            window.engine.on('viewEnv.onDataChanged', render);
        }
        if (window.viewEnv && typeof viewEnv.addDataChangedCallback === 'function') {
            try {
                viewEnv.addDataChangedCallback('model', 0, true);
            } catch (e) {}
        }
        window.setInterval(poll, 200);
        if (window.model && typeof window.model.onReady === 'function') {
            window.model.onReady({});
        }
    }

    function afterFrames() {
        requestAnimationFrame(function () {
            requestAnimationFrame(initialize);
        });
    }

    if (window.engine && window.engine.whenReady) {
        var domReady = window.isDomBuilt ? Promise.resolve() : new Promise(function (resolve) {
            window.engine.on('self.onDomBuilt', resolve);
        });
        Promise.all([window.engine.whenReady, domReady]).then(afterFrames);
    } else {
        afterFrames();
    }
}());