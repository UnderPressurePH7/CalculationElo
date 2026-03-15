package com.github.under.calculationelo
{
    import flash.display.Sprite;
    import flash.display.Shape;
    import flash.display.GradientType;
    import flash.display.SpreadMethod;
    import flash.display.Graphics;
    import flash.text.TextField;
    import flash.text.TextFieldAutoSize;
    import flash.filters.DropShadowFilter;
    import flash.geom.Matrix;
    import flash.geom.Point;
    import flash.events.MouseEvent;
    import flash.utils.clearTimeout;
    import flash.utils.setTimeout;
    import net.wg.data.constants.Cursors;

    public class EloPanelComponent extends EloBattleDisplayable
    {
        private static const BASE_WIDTH:int = 140;
        private static const BASE_HEIGHT:int = 110;

        private static const PAD_SIDE:int = 5;
        private static const PAD_TOP:int = 5;
        private static const PAD_BOTTOM:int = 5;
        private static const ROW_GAP_HEADER:int = 22;
        private static const ROW_GAP_NAMES:int = 22;
        private static const ROW_GAP_RATING:int = 24;
        private static const ROW_GAP_SMALL:int = 18;
        private static const RATING_INSET:int = 15;
        private static const SMALL_INSET:int = 20;
        private static const MAX_NAME_CHARS:int = 6;
        private static const AUTOSIZE_GUTTER:int = 4;

        private static const BOUNDARY_GAP:int = 5;
        private static const DRAG_DELAY:int = 150;
        private static const DRAG_THRESHOLD:int = 20;

        private static const FONT_FACE:String = "Tahoma";

        private static const BG_COLOR_TOP:uint = 0x1a1a2e;
        private static const BG_COLOR_BOTTOM:uint = 0x0d0d1a;
        private static const BG_ALPHA_TOP:Number = 0.35;
        private static const BG_ALPHA_BOTTOM:Number = 0.35;
        private static const BG_BORDER_COLOR:uint = 0x444466;
        private static const BG_BORDER_ALPHA:Number = 0.4;
        private static const BG_CORNER_RADIUS:int = 6;

        private var _background:Shape;
        private var _dragHit:Sprite;

        private var _headerField:TextField;
        private var _alliesNameField:TextField;
        private var _enemiesNameField:TextField;
        private var _alliesRatingField:TextField;
        private var _enemiesRatingField:TextField;
        private var _eloGainField:TextField;
        private var _eloLossField:TextField;
        private var _enemyStatsField:TextField;

        private var _textShadow:DropShadowFilter;

        private var _scaleFactor:Number = 1.0;
        private var _panelWidth:int = BASE_WIDTH;
        private var _panelHeight:int = BASE_HEIGHT;

        private var _offset:Array = [0, 0];
        private var _isDragging:Boolean = false;
        private var _isDragTest:Boolean = false;
        private var _dragTimeout:uint = 0;
        private var _clickPoint:Point;
        private var _clickOffset:Point;
        private var _reusablePoint:Point;

        private var _initialized:Boolean = false;
        private var _disposed:Boolean = false;
        private var _cleanedUp:Boolean = false;

        private var _showTitle:Boolean = false;
        private var _showTeamNames:Boolean = true;
        private var _showEloChanges:Boolean = true;
        private var _showWinrateAndBattles:Boolean = true;

        private var _headerText:String = "ELO Calculator";
        private var _headerColor:uint = 0xFFFFFF;
        private var _alliesNamesColor:uint = 0x4F8627;
        private var _enemiesNamesColor:uint = 0x9A0101;
        private var _alliesRatingColor:uint = 0x4F8627;
        private var _enemiesRatingColor:uint = 0x9A0101;
        private var _eloGainColor:uint = 0x00FF00;
        private var _eloLossColor:uint = 0xFF0000;

        private var _cachedAlliesName:String = " ";
        private var _cachedEnemiesName:String = " ";
        private var _cachedAlliesRating:int = 0;
        private var _cachedEnemiesRating:int = 0;
        private var _cachedEloPlus:int = 0;
        private var _cachedEloMinus:int = 0;
        private var _cachedWinsPercent:int = 0;
        private var _cachedBattlesCount:int = 0;

        public function EloPanelComponent()
        {
            super();
            mouseEnabled = false;
            mouseChildren = true;
            _clickPoint = new Point();
            _clickOffset = new Point();
            _reusablePoint = new Point();
        }

        override protected function onPopulate():void
        {
            super.onPopulate();
            _textShadow = new DropShadowFilter(1, 45, 0x000000, 0.7, 2, 2, 1, 1);
            _createBackground();
            _createTextFields();
            _createDragHit();
            _initialized = true;
            visible = false;
            _setupDragListeners();
        }

        override protected function onDispose():void
        {
            if (_disposed) return;
            _disposed = true;
            _performFullCleanup();
            _disposeTextField(_headerField);
            _disposeTextField(_alliesNameField);
            _disposeTextField(_enemiesNameField);
            _disposeTextField(_alliesRatingField);
            _disposeTextField(_enemiesRatingField);
            _disposeTextField(_eloGainField);
            _disposeTextField(_eloLossField);
            _disposeTextField(_enemyStatsField);
            _headerField = null;
            _alliesNameField = null;
            _enemiesNameField = null;
            _alliesRatingField = null;
            _enemiesRatingField = null;
            _eloGainField = null;
            _eloLossField = null;
            _enemyStatsField = null;
            if (_background)
            {
                _background.graphics.clear();
                if (contains(_background)) removeChild(_background);
                _background = null;
            }
            if (_dragHit)
            {
                _dragHit.graphics.clear();
                _dragHit.buttonMode = false;
                _dragHit.useHandCursor = false;
                if (contains(_dragHit)) removeChild(_dragHit);
                _dragHit = null;
            }
            _textShadow = null;
            _offset = null;
            _clickPoint = null;
            _clickOffset = null;
            _reusablePoint = null;
            _initialized = false;
            super.onDispose();
        }

        public function cleanup():void
        {
            if (_cleanedUp) return;
            _performFullCleanup();
        }

        private function _performFullCleanup():void
        {
            if (_cleanedUp) return;
            _cleanedUp = true;
            _teardownDragListeners();
            _clearDragTimeout();
            _resetCursor();
            _isDragging = false;
            _isDragTest = false;
            finiBattle();
            if (parent)
            {
                parent.removeChild(this);
            }
            battlePage = null;
            componentName = null;
        }

        override protected function onResized():void
        {
            if (_disposed || _isDragging) return;
            _syncPosition();
        }

        private function _createBackground():void
        {
            _background = new Shape();
            addChild(_background);
        }

        private function _createTextFields():void
        {
            _headerField = _makeHtmlField();
            _alliesNameField = _makeHtmlField();
            _enemiesNameField = _makeHtmlField();
            _alliesRatingField = _makeHtmlField();
            _enemiesRatingField = _makeHtmlField();
            _eloGainField = _makeHtmlField();
            _eloLossField = _makeHtmlField();
            _enemyStatsField = _makeHtmlField();
            addChild(_headerField);
            addChild(_alliesNameField);
            addChild(_enemiesNameField);
            addChild(_alliesRatingField);
            addChild(_enemiesRatingField);
            addChild(_eloGainField);
            addChild(_eloLossField);
            addChild(_enemyStatsField);
        }

        private function _createDragHit():void
        {
            _dragHit = new Sprite();
            _dragHit.buttonMode = true;
            _dragHit.useHandCursor = true;
            _redrawDragHit();
            addChild(_dragHit);
        }

        private function _redrawDragHit():void
        {
            if (!_dragHit) return;
            _dragHit.graphics.clear();
            _dragHit.graphics.beginFill(0x000000, 0.0);
            _dragHit.graphics.drawRect(0, 0, _panelWidth, _panelHeight);
            _dragHit.graphics.endFill();
        }

        private function _makeHtmlField():TextField
        {
            var tf:TextField = new TextField();
            tf.selectable = false;
            tf.mouseEnabled = false;
            tf.autoSize = TextFieldAutoSize.LEFT;
            tf.multiline = false;
            tf.wordWrap = false;
            tf.filters = [_textShadow];
            return tf;
        }

        private function _disposeTextField(tf:TextField):void
        {
            if (tf == null) return;
            tf.filters = [];
            tf.htmlText = "";
            if (contains(tf)) removeChild(tf);
        }

        private function _setupDragListeners():void
        {
            if (!_dragHit) return;
            _dragHit.addEventListener(MouseEvent.MOUSE_DOWN, _onDragMouseDown);
            _dragHit.addEventListener(MouseEvent.MOUSE_OVER, _onDragMouseOver);
            _dragHit.addEventListener(MouseEvent.MOUSE_OUT, _onDragMouseOut);
        }

        private function _teardownDragListeners():void
        {
            if (_dragHit)
            {
                _dragHit.removeEventListener(MouseEvent.MOUSE_DOWN, _onDragMouseDown);
                _dragHit.removeEventListener(MouseEvent.MOUSE_OVER, _onDragMouseOver);
                _dragHit.removeEventListener(MouseEvent.MOUSE_OUT, _onDragMouseOut);
            }
            _removeStageListeners();
        }

        private function _addStageListeners():void
        {
            if (stage)
            {
                stage.addEventListener(MouseEvent.MOUSE_UP, _onDragMouseUp);
                stage.addEventListener(MouseEvent.MOUSE_MOVE, _onDragMouseMove);
            }
        }

        private function _removeStageListeners():void
        {
            if (stage)
            {
                stage.removeEventListener(MouseEvent.MOUSE_UP, _onDragMouseUp);
                stage.removeEventListener(MouseEvent.MOUSE_MOVE, _onDragMouseMove);
            }
        }

        private function _clearDragTimeout():void
        {
            if (_dragTimeout != 0)
            {
                clearTimeout(_dragTimeout);
                _dragTimeout = 0;
            }
        }

        private function _resetCursor():void
        {
            try
            {
                App.cursor.forceSetCursor(Cursors.ARROW);
            }
            catch (e:Error) {}
        }

        private function _onDragMouseDown(e:MouseEvent):void
        {
            if (_disposed || _cleanedUp || !stage) return;
            _clickPoint.x = stage.mouseX;
            _clickPoint.y = stage.mouseY;
            _clickOffset.x = x - _clickPoint.x;
            _clickOffset.y = y - _clickPoint.y;
            _isDragTest = true;
            _clearDragTimeout();
            _dragTimeout = setTimeout(_beginDrag, DRAG_DELAY);
            _addStageListeners();
        }

        private function _beginDrag():void
        {
            _isDragTest = false;
            _isDragging = true;
            _dragTimeout = 0;
            App.cursor.forceSetCursor(Cursors.MOVE);
        }

        private function _onDragMouseMove(e:MouseEvent):void
        {
            if (_disposed || _cleanedUp || !stage) return;
            if (!_isDragging && _isDragTest)
            {
                var dx:Number = stage.mouseX - _clickPoint.x;
                var dy:Number = stage.mouseY - _clickPoint.y;
                if (dx * dx + dy * dy > DRAG_THRESHOLD * DRAG_THRESHOLD)
                {
                    _clearDragTimeout();
                    _beginDrag();
                    return;
                }
            }
            if (_isDragging)
            {
                _clampToScreen(_clickOffset.x + stage.mouseX, _clickOffset.y + stage.mouseY);
                x = _reusablePoint.x;
                y = _reusablePoint.y;
            }
        }

        private function _onDragMouseUp(e:MouseEvent):void
        {
            _clearDragTimeout();
            if (_isDragging)
            {
                _getAnchor();
                _offset[0] = int(x - _reusablePoint.x);
                _offset[1] = int(y - _reusablePoint.y);
                _syncPosition();
                App.cursor.forceSetCursor(Cursors.DRAG_OPEN);
                dispatchEvent(new EloPanelEvent(EloPanelEvent.OFFSET_CHANGED, _offset));
            }
            _isDragTest = false;
            _isDragging = false;
            _removeStageListeners();
        }

        private function _onDragMouseOver(e:MouseEvent):void
        {
            if (_disposed || _cleanedUp) return;
            App.cursor.forceSetCursor(Cursors.DRAG_OPEN);
        }

        private function _onDragMouseOut(e:MouseEvent):void
        {
            if (_disposed || _cleanedUp) return;
            if (!_isDragging)
            {
                App.cursor.forceSetCursor(Cursors.ARROW);
            }
        }

        private function _getAnchor():void
        {
            _reusablePoint.x = int(App.appWidth * 0.5 - _panelWidth * 0.5);
            _reusablePoint.y = BOUNDARY_GAP;
        }

        private function _clampToScreen(px:Number, py:Number):void
        {
            _reusablePoint.x = int(Math.max(BOUNDARY_GAP, Math.min(App.appWidth - _panelWidth - BOUNDARY_GAP, px)));
            _reusablePoint.y = int(Math.max(BOUNDARY_GAP, Math.min(App.appHeight - _panelHeight - BOUNDARY_GAP, py)));
        }

        private function _syncPosition():void
        {
            if (_isDragging || _disposed) return;
            _getAnchor();
            var ax:int = _reusablePoint.x;
            var ay:int = _reusablePoint.y;
            _clampToScreen(ax + _offset[0], ay + _offset[1]);
            x = _reusablePoint.x;
            y = _reusablePoint.y;
        }

        private function _drawBackground():void
        {
            if (!_background || _disposed) return;
            var g:Graphics = _background.graphics;
            g.clear();
            var matrix:Matrix = new Matrix();
            matrix.createGradientBox(_panelWidth, _panelHeight, Math.PI / 2, 0, 0);
            g.beginGradientFill(
                GradientType.LINEAR,
                [BG_COLOR_TOP, BG_COLOR_BOTTOM],
                [BG_ALPHA_TOP, BG_ALPHA_BOTTOM],
                [0, 255],
                matrix,
                SpreadMethod.PAD
            );
            g.drawRoundRect(0, 0, _panelWidth, _panelHeight, BG_CORNER_RADIUS, BG_CORNER_RADIUS);
            g.endFill();
            g.lineStyle(1, BG_BORDER_COLOR, BG_BORDER_ALPHA);
            g.drawRoundRect(0, 0, _panelWidth, _panelHeight, BG_CORNER_RADIUS, BG_CORNER_RADIUS);
        }

        private function _s(val:int):int
        {
            return int(val * _scaleFactor);
        }

        private function _layoutFields():void
        {
            if (_disposed) return;

            var currentY:int = _s(PAD_TOP);
            var ratingSize:int = _s(20);
            var nameSize:int = _s(16);
            var smallSize:int = _s(14);
            var headerSize:int = _s(14);

            if (_showTitle)
            {
                _headerField.visible = true;
                _headerField.htmlText = _fmt(_escapeHtml(_headerText), headerSize, _headerColor);
                _headerField.x = int((_panelWidth - _headerField.textWidth) / 2);
                _headerField.y = currentY;
                currentY += _s(ROW_GAP_HEADER);
            }
            else
            {
                _headerField.visible = false;
            }

            if (_showTeamNames)
            {
                _alliesNameField.visible = true;
                _enemiesNameField.visible = true;
                _alliesNameField.htmlText = _fmt(_escapeHtml(_truncate(_cachedAlliesName, MAX_NAME_CHARS)), nameSize, _alliesNamesColor);
                _enemiesNameField.htmlText = _fmt(_escapeHtml(_truncate(_cachedEnemiesName, MAX_NAME_CHARS)), nameSize, _enemiesNamesColor);
                _alliesNameField.x = _s(PAD_SIDE);
                _alliesNameField.y = currentY;
                _enemiesNameField.x = _panelWidth - _enemiesNameField.textWidth - _s(PAD_SIDE) - AUTOSIZE_GUTTER;
                _enemiesNameField.y = currentY;
                currentY += _s(ROW_GAP_NAMES);
            }
            else
            {
                _alliesNameField.visible = false;
                _enemiesNameField.visible = false;
            }

            _alliesRatingField.visible = true;
            _enemiesRatingField.visible = true;
            _alliesRatingField.htmlText = _fmt(_cachedAlliesRating > 0 ? String(_cachedAlliesRating) : " ", ratingSize, _alliesRatingColor);
            _enemiesRatingField.htmlText = _fmt(_cachedEnemiesRating > 0 ? String(_cachedEnemiesRating) : " ", ratingSize, _enemiesRatingColor);
            _alliesRatingField.x = _s(RATING_INSET);
            _alliesRatingField.y = currentY;
            _enemiesRatingField.x = _panelWidth - _enemiesRatingField.textWidth - _s(RATING_INSET) - AUTOSIZE_GUTTER;
            _enemiesRatingField.y = currentY;
            currentY += _s(ROW_GAP_RATING);

            if (_showEloChanges)
            {
                _eloGainField.visible = true;
                _eloLossField.visible = true;
                _eloGainField.htmlText = _fmt(_cachedEloPlus > 0 ? ("+" + _cachedEloPlus) : "", smallSize, _eloGainColor);
                _eloLossField.htmlText = _fmt(_cachedEloMinus < 0 ? String(_cachedEloMinus) : "", smallSize, _eloLossColor);
                _eloGainField.x = _s(SMALL_INSET);
                _eloGainField.y = currentY;
                _eloLossField.x = _panelWidth - _eloLossField.textWidth - _s(SMALL_INSET) - AUTOSIZE_GUTTER;
                _eloLossField.y = currentY;
                currentY += _s(ROW_GAP_SMALL);
            }
            else
            {
                _eloGainField.visible = false;
                _eloLossField.visible = false;
            }

            if (_showWinrateAndBattles)
            {
                _enemyStatsField.visible = true;
                var statsHtml:String = _buildStatsHtml(_cachedBattlesCount, _cachedWinsPercent, smallSize);
                _enemyStatsField.htmlText = statsHtml;
                _enemyStatsField.x = int((_panelWidth - _enemyStatsField.textWidth) / 2);
                _enemyStatsField.y = currentY;
                currentY += _s(ROW_GAP_SMALL);
            }
            else
            {
                _enemyStatsField.visible = false;
            }

            _panelHeight = currentY + _s(PAD_BOTTOM);
            _drawBackground();
            _redrawDragHit();
        }

        private function _fmt(text:String, size:int, color:uint):String
        {
            return '<font face="' + FONT_FACE + '" size="' + size + '" color="' + _colorToHex(color) + '"><b>' + text + '</b></font>';
        }

        private function _truncate(name:String, maxLen:int):String
        {
            if (!name || name == "Unknown" || name == " ") return " ";
            if (name.length > maxLen) return name.substr(0, maxLen).toUpperCase();
            return name.toUpperCase();
        }

        private static function _escapeHtml(text:String):String
        {
            if (!text) return "";
            text = text.split("&").join("&amp;");
            text = text.split("<").join("&lt;");
            text = text.split(">").join("&gt;");
            text = text.split('"').join("&quot;");
            return text;
        }

        private function _buildStatsHtml(battles:int, winrate:int, size:int):String
        {
            if (battles <= 0 && winrate <= 0) return "";
            var parts:Array = [];
            if (battles > 0)
            {
                parts.push('<font face="' + FONT_FACE + '" size="' + size + '" color="'
                    + _colorToHex(_getBattlesColor(battles)) + '"><b>' + battles + '</b></font>');
            }
            if (winrate > 0)
            {
                parts.push('<font face="' + FONT_FACE + '" size="' + size + '" color="'
                    + _colorToHex(_getWinrateColor(winrate)) + '"><b>(' + winrate + '%)</b></font>');
            }
            return parts.join(" ");
        }

        private function _getWinrateColor(wr:int):uint
        {
            if (wr < 47) return 0xFE0E00;
            if (wr < 49) return 0xFE7903;
            if (wr < 52) return 0xF8F400;
            if (wr < 57) return 0x60FF00;
            if (wr < 64) return 0x02C9B3;
            return 0xD042F3;
        }

        private function _getBattlesColor(b:int):uint
        {
            if (b < 50)  return 0xAAAAAA;
            if (b < 100) return 0xFFFFFF;
            return 0x60FF00;
        }

        private static function _colorToHex(color:uint):String
        {
            var hex:String = color.toString(16).toUpperCase();
            while (hex.length < 6) hex = "0" + hex;
            return "#" + hex;
        }

        public function as_updateState(
            alliesName:String, enemiesName:String,
            alliesRating:int, enemiesRating:int,
            eloPlus:int, eloMinus:int,
            winsPercent:int, battlesCount:int
        ):void
        {
            if (!_initialized || _disposed) return;
            _cachedAlliesName = alliesName;
            _cachedEnemiesName = enemiesName;
            _cachedAlliesRating = alliesRating;
            _cachedEnemiesRating = enemiesRating;
            _cachedEloPlus = eloPlus;
            _cachedEloMinus = eloMinus;
            _cachedWinsPercent = winsPercent;
            _cachedBattlesCount = battlesCount;
            _layoutFields();
        }

        public function as_setVisible(isVisible:Boolean):void
        {
            if (_disposed) return;
            this.visible = isVisible;
        }

        public function as_setPosition(offset:Array):void
        {
            if (!_initialized || _disposed) return;
            if (offset && offset.length >= 2)
            {
                _offset[0] = int(offset[0]);
                _offset[1] = int(offset[1]);
            }
            _syncPosition();
        }

        public function as_setScale(factor:Number):void
        {
            if (!_initialized || _disposed) return;
            _scaleFactor = factor;
            _panelWidth = int(BASE_WIDTH * _scaleFactor);
            if (_textShadow)
            {
                _textShadow.distance = _s(1);
                _textShadow.blurX = _s(2);
                _textShadow.blurY = _s(2);
            }
            _layoutFields();
            _syncPosition();
        }

        public function as_updateConfig(
            showTitle:Boolean, showTeamNames:Boolean,
            showEloChanges:Boolean, showWinrateAndBattles:Boolean,
            headerText:String, headerColor:uint,
            alliesNamesColor:uint, enemiesNamesColor:uint,
            alliesRatingColor:uint, enemiesRatingColor:uint,
            eloGainColor:uint, eloLossColor:uint
        ):void
        {
            if (_disposed) return;
            _showTitle = showTitle;
            _showTeamNames = showTeamNames;
            _showEloChanges = showEloChanges;
            _showWinrateAndBattles = showWinrateAndBattles;
            _headerText = headerText;
            _headerColor = headerColor;
            _alliesNamesColor = alliesNamesColor;
            _enemiesNamesColor = enemiesNamesColor;
            _alliesRatingColor = alliesRatingColor;
            _enemiesRatingColor = enemiesRatingColor;
            _eloGainColor = eloGainColor;
            _eloLossColor = eloLossColor;
            if (_initialized) _layoutFields();
        }
    }
}
