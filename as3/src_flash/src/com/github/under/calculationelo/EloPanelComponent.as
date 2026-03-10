package com.github.under.calculationelo
{
    import flash.display.Sprite;
    import flash.display.Shape;
    import flash.display.Bitmap;
    import flash.display.BitmapData;
    import flash.display.Loader;
    import flash.display.GradientType;
    import flash.display.SpreadMethod;
    import flash.display.Graphics;
    import flash.display.DisplayObject;
    import flash.text.TextField;
    import flash.text.TextFieldAutoSize;
    import flash.filters.DropShadowFilter;
    import flash.geom.Matrix;
    import flash.geom.Point;
    import flash.events.Event;
    import flash.events.IOErrorEvent;
    import flash.events.MouseEvent;
    import flash.net.URLRequest;
    import net.wg.data.constants.Cursors;

    public class EloPanelComponent extends EloBattleDisplayable
    {
        private static const BASE_WIDTH:int = 140;
        private static const BASE_HEIGHT:int = 110;
        private static const BOUNDARY_GAP:int = 5;
        private static const BACKGROUND_IMAGE:String = 'img://gui/maps/icons/tanksetup/popular_loadouts/legendary_bg.png';

        public var updatePosition:Function = null;

        private var _panel:Sprite;
        private var _dragArea:Sprite;
        private var _background:Shape;
        private var _bgImageHolder:Sprite;
        private var _bgImageLoaded:Boolean = false;
        private var _bgBitmap:Bitmap = null;
        private var _bgBitmapData:BitmapData = null;
        private var _bgLoader:Loader = null;
        private var _bgMaskShape:Shape = null;

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
        private var _initialized:Boolean = false;
        private var _disposed:Boolean = false;

        private var _showTitle:Boolean = false;
        private var _showTeamNames:Boolean = true;
        private var _showEloChanges:Boolean = true;
        private var _showWinrateAndBattles:Boolean = true;

        private var _headerText:String = "ELO Calculator";
        private var _headerColor:String = "#FFFFFF";
        private var _alliesNamesColor:String = "#4F8627";
        private var _enemiesNamesColor:String = "#9A0101";
        private var _alliesRatingColor:String = "#4F8627";
        private var _enemiesRatingColor:String = "#9A0101";
        private var _eloGainColor:String = "#00FF00";
        private var _eloLossColor:String = "#FF0000";

        public function EloPanelComponent()
        {
            super();
            mouseEnabled = false;
        }

        override protected function onPopulate():void
        {
            super.onPopulate();
            _createShadowFilter();
            _createPanel();
            _createDragArea();
            _createBackgroundImageHolder();
            _createBackground();
            _createTextFields();
            _loadBackgroundImage();
            _initialized = true;
            visible = false;

            _dragArea.addEventListener(MouseEvent.MOUSE_DOWN, _onMouseDown);
            _dragArea.addEventListener(MouseEvent.MOUSE_OVER, _onMouseOver);
            _dragArea.addEventListener(MouseEvent.MOUSE_OUT, _onMouseOut);
        }

        override protected function onDispose():void
        {
            if (_disposed) return;
            _disposed = true;

            _dragArea.removeEventListener(MouseEvent.MOUSE_DOWN, _onMouseDown);
            _dragArea.removeEventListener(MouseEvent.MOUSE_OVER, _onMouseOver);
            _dragArea.removeEventListener(MouseEvent.MOUSE_OUT, _onMouseOut);
            _removeStageDragListeners();

            _cleanupLoader();
            _disposeBgBitmapData();

            _clearBgImageHolder();

            if (_bgImageHolder)
            {
                _bgImageHolder.mask = null;
            }
            _bgMaskShape = null;

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
                if (_panel && _panel.contains(_background))
                {
                    _panel.removeChild(_background);
                }
                _background = null;
            }

            if (_bgImageHolder)
            {
                if (_panel && _panel.contains(_bgImageHolder))
                {
                    _panel.removeChild(_bgImageHolder);
                }
                _bgImageHolder = null;
            }

            if (_panel)
            {
                _panel.mouseEnabled = false;
                _panel.mouseChildren = false;
                if (contains(_panel))
                {
                    removeChild(_panel);
                }
                _panel = null;
            }

            if (_dragArea)
            {
                _dragArea.graphics.clear();
                _dragArea.buttonMode = false;
                _dragArea.useHandCursor = false;
                if (contains(_dragArea))
                {
                    removeChild(_dragArea);
                }
                _dragArea = null;
            }

            _textShadow = null;
            updatePosition = null;

            _offset = null;
            _initialized = false;

            super.onDispose();
        }

        override protected function onResized():void
        {
            if (_disposed) return;
            _syncPositions();
        }

        private function _disposeTextField(tf:TextField):void
        {
            if (tf == null) return;
            tf.filters = [];
            tf.htmlText = "";
            if (_panel && _panel.contains(tf))
            {
                _panel.removeChild(tf);
            }
        }

        private function _disposeBgBitmapData():void
        {
            if (_bgBitmapData)
            {
                try
                {
                    _bgBitmapData.dispose();
                }
                catch (err:Error) {}
                _bgBitmapData = null;
            }
            _bgBitmap = null;
        }

        private function _clearBgImageHolder():void
        {
            if (!_bgImageHolder) return;

            while (_bgImageHolder.numChildren > 0)
            {
                var child:DisplayObject = _bgImageHolder.removeChildAt(0);
                if (child is Bitmap)
                {
                    var bmp:Bitmap = child as Bitmap;
                    bmp.bitmapData = null;
                }
                else if (child is Shape)
                {
                    (child as Shape).graphics.clear();
                }
            }
            _bgImageHolder.mask = null;
        }


        private function _cleanupLoader():void
        {
            if (_bgLoader)
            {
                try
                {
                    _bgLoader.contentLoaderInfo.removeEventListener(Event.COMPLETE, _onBgImageLoaded);
                    _bgLoader.contentLoaderInfo.removeEventListener(IOErrorEvent.IO_ERROR, _onBgImageError);
                }
                catch (err:Error) {}

                try
                {
                    _bgLoader.unloadAndStop();
                }
                catch (err:Error) {}
                _bgLoader = null;
            }
        }


        private function _onMouseDown(e:MouseEvent):void
        {
            if (_disposed) return;
            _isDragging = true;
            App.cursor.forceSetCursor(Cursors.MOVE);
            _dragArea.startDrag();
            if (stage)
            {
                stage.addEventListener(MouseEvent.MOUSE_UP, _onMouseUp);
                stage.addEventListener(MouseEvent.MOUSE_MOVE, _onMouseMove);
            }
        }

        private function _onMouseMove(e:MouseEvent):void
        {
            if (_isDragging && _panel && _dragArea)
            {
                var clamped:Point = _clampToScreen(_dragArea.x, _dragArea.y);
                _panel.x = clamped.x;
                _panel.y = clamped.y;
            }
        }

        private function _onMouseUp(e:MouseEvent):void
        {
            if (_isDragging)
            {
                _isDragging = false;
                if (_dragArea) _dragArea.stopDrag();
                _removeStageDragListeners();
                App.cursor.forceSetCursor(Cursors.ARROW);

                if (!_dragArea || _disposed) return;

                var anchor:Point = _getAnchor();
                var clamped:Point = _clampToScreen(_dragArea.x, _dragArea.y);
                _offset = [
                    int((clamped.x - anchor.x) * App.appScale),
                    int((clamped.y - anchor.y) * App.appScale)
                ];
                _syncPositions();

                if (updatePosition != null)
                {
                    updatePosition(_offset);
                }
            }
        }

        private function _removeStageDragListeners():void
        {
            if (stage)
            {
                stage.removeEventListener(MouseEvent.MOUSE_UP, _onMouseUp);
                stage.removeEventListener(MouseEvent.MOUSE_MOVE, _onMouseMove);
            }
        }

        private function _onMouseOver(e:MouseEvent):void
        {
            if (_disposed) return;
            App.cursor.forceSetCursor(Cursors.DRAG_OPEN);
        }

        private function _onMouseOut(e:MouseEvent):void
        {
            if (_disposed) return;
            if (!_isDragging)
            {
                App.cursor.forceSetCursor(Cursors.ARROW);
            }
        }

        private function _getAnchor():Point
        {
            return new Point(
                int(App.appWidth * 0.5 - _panelWidth * 0.5),
                BOUNDARY_GAP
            );
        }

        private function _clampToScreen(px:Number, py:Number):Point
        {
            var cx:int = int(Math.max(BOUNDARY_GAP, Math.min(App.appWidth - _panelWidth - BOUNDARY_GAP, px)));
            var cy:int = int(Math.max(BOUNDARY_GAP, Math.min(App.appHeight - _panelHeight - BOUNDARY_GAP, py)));
            return new Point(cx, cy);
        }

        private function _syncPositions():void
        {
            if (_isDragging || _disposed || !_panel || !_dragArea) return;

            var anchor:Point = _getAnchor();
            var targetX:Number = anchor.x + _offset[0] / App.appScale;
            var targetY:Number = anchor.y + _offset[1] / App.appScale;
            var clamped:Point = _clampToScreen(targetX, targetY);

            _panel.x = _dragArea.x = clamped.x;
            _panel.y = _dragArea.y = clamped.y;
        }

        private function _createShadowFilter():void
        {
            _textShadow = new DropShadowFilter(1, 45, 0x000000, 0.7, 2, 2, 1, 1);
        }

        private function _createPanel():void
        {
            _panel = new Sprite();
            _panel.mouseEnabled = false;
            _panel.mouseChildren = false;
            addChild(_panel);
        }

        private function _createDragArea():void
        {
            _dragArea = new Sprite();
            _dragArea.graphics.beginFill(0x000000, 0.0);
            _dragArea.graphics.drawRect(0, 0, _panelWidth, _panelHeight);
            _dragArea.graphics.endFill();
            _dragArea.buttonMode = true;
            _dragArea.useHandCursor = true;
            addChild(_dragArea);
        }

        private function _updateDragArea():void
        {
            if (!_dragArea) return;
            _dragArea.graphics.clear();
            _dragArea.graphics.beginFill(0x000000, 0.0);
            _dragArea.graphics.drawRect(0, 0, _panelWidth, _panelHeight);
            _dragArea.graphics.endFill();
        }

        private function _createBackgroundImageHolder():void
        {
            _bgImageHolder = new Sprite();
            _panel.addChild(_bgImageHolder);
        }

        private function _loadBackgroundImage():void
        {
            try
            {
                _bgLoader = new Loader();
                _bgLoader.contentLoaderInfo.addEventListener(Event.COMPLETE, _onBgImageLoaded);
                _bgLoader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR, _onBgImageError);
                _bgLoader.load(new URLRequest(BACKGROUND_IMAGE));
            }
            catch (err:Error) {}
        }

        private function _onBgImageLoaded(e:Event):void
        {
            if (_disposed) return;

            try
            {
                var loader:Loader = e.target.loader as Loader;
                if (loader && loader.content)
                {
                    _bgBitmap = loader.content as Bitmap;
                    if (_bgBitmap && _bgBitmap.bitmapData)
                    {
                        _bgBitmapData = _bgBitmap.bitmapData;
                        _bgImageLoaded = true;
                        _updateBgImage();
                        _drawBackground();
                    }
                }
            }
            catch (err:Error) {}
            finally
            {
                _cleanupLoader();
            }
        }

        private function _onBgImageError(e:IOErrorEvent):void
        {
            _bgImageLoaded = false;
            _cleanupLoader();
        }

        private function _updateBgImage():void
        {
            if (!_bgImageHolder || _disposed) return;

            _clearBgImageHolder();

            if (!_bgImageLoaded || !_bgBitmapData) return;

            var bmp:Bitmap = new Bitmap(_bgBitmapData, "auto", true);
            bmp.width = _panelWidth;
            bmp.height = _panelHeight;
            bmp.alpha = 0.75;
            _bgImageHolder.addChild(bmp);

            _bgMaskShape = new Shape();
            _bgMaskShape.graphics.beginFill(0xFFFFFF);
            _bgMaskShape.graphics.drawRoundRect(0, 0, _panelWidth, _panelHeight, 6, 6);
            _bgMaskShape.graphics.endFill();
            _bgImageHolder.addChild(_bgMaskShape);
            _bgImageHolder.mask = _bgMaskShape;
        }

        private function _createBackground():void
        {
            _background = new Shape();
            _drawBackground();
            _panel.addChild(_background);
        }

        private function _drawBackground():void
        {
            if (!_background || _disposed) return;

            var g:Graphics = _background.graphics;
            g.clear();

            var matrix:Matrix = new Matrix();
            matrix.createGradientBox(_panelWidth, _panelHeight, Math.PI / 2, 0, 0);

            var a1:Number = _bgImageLoaded ? 0.45 : 0.85;
            var a2:Number = _bgImageLoaded ? 0.55 : 0.9;

            g.beginGradientFill(GradientType.LINEAR, [0x1a1a2e, 0x0d0d1a], [a1, a2], [0, 255], matrix, SpreadMethod.PAD);
            g.drawRoundRect(0, 0, _panelWidth, _panelHeight, 6, 6);
            g.endFill();

            g.lineStyle(1, 0x444466, 0.5);
            g.drawRoundRect(0, 0, _panelWidth, _panelHeight, 6, 6);
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

            _panel.addChild(_headerField);
            _panel.addChild(_enemiesNameField);
            _panel.addChild(_alliesNameField);
            _panel.addChild(_alliesRatingField);
            _panel.addChild(_enemiesRatingField);
            _panel.addChild(_eloGainField);
            _panel.addChild(_eloLossField);
            _panel.addChild(_enemyStatsField);
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

        public function as_updateState(
            alliesName:String, enemiesName:String,
            alliesRating:int, enemiesRating:int,
            eloPlus:int, eloMinus:int,
            winsPercent:int, battlesCount:int
        ):void
        {
            if (!_initialized || _disposed) return;
            _updateDisplay(alliesName, enemiesName, alliesRating, enemiesRating,
                           eloPlus, eloMinus, winsPercent, battlesCount);
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
                _offset = [int(offset[0]), int(offset[1])];
            }
            _syncPositions();
        }

        public function as_setScale(factor:Number):void
        {
            if (!_initialized || _disposed) return;
            _scaleFactor = factor;
            _panelWidth = int(BASE_WIDTH * _scaleFactor);
            _panelHeight = int(BASE_HEIGHT * _scaleFactor);

            if (_textShadow)
            {
                _textShadow.distance = _s(1);
                _textShadow.blurX = _s(2);
                _textShadow.blurY = _s(2);
            }

            _updateDragArea();
            _layoutFields();
            _syncPositions();
        }

        public function as_updateConfig(
            showTitle:Boolean, showTeamNames:Boolean,
            showEloChanges:Boolean, showWinrateAndBattles:Boolean,
            headerText:String, headerColor:String,
            alliesNamesColor:String, enemiesNamesColor:String,
            alliesRatingColor:String, enemiesRatingColor:String,
            eloGainColor:String, eloLossColor:String
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


        private function _layoutFields():void
        {
            if (_disposed) return;

            var currentY:int = _s(5);
            var centerX:int = _panelWidth / 2;

            if (_showTitle)
            {
                _headerField.visible = true;
                _headerField.htmlText = _fmt(_headerText, _s(14), _headerColor);
                _headerField.x = centerX - _headerField.textWidth / 2;
                _headerField.y = currentY;
                currentY += _s(22);
            }
            else _headerField.visible = false;

            if (_showTeamNames)
            {
                _alliesNameField.visible = true;
                _enemiesNameField.visible = true;
                _alliesNameField.x = _s(5);
                _alliesNameField.y = currentY;
                _enemiesNameField.y = currentY;
                currentY += _s(22);
            }
            else
            {
                _alliesNameField.visible = false;
                _enemiesNameField.visible = false;
            }

            _alliesRatingField.visible = true;
            _enemiesRatingField.visible = true;
            _alliesRatingField.x = _s(15);
            _alliesRatingField.y = currentY;
            _enemiesRatingField.y = currentY;
            currentY += _s(24);

            if (_showEloChanges)
            {
                _eloGainField.visible = true;
                _eloLossField.visible = true;
                _eloGainField.x = _s(20);
                _eloGainField.y = currentY;
                _eloLossField.y = currentY;
                currentY += _s(18);
            }
            else
            {
                _eloGainField.visible = false;
                _eloLossField.visible = false;
            }

            if (_showWinrateAndBattles)
            {
                _enemyStatsField.visible = true;
                _enemyStatsField.y = currentY;
                currentY += _s(18);
            }
            else _enemyStatsField.visible = false;

            _panelHeight = currentY + _s(5);
            _updateDragArea();
            _updateBgImage();
            _drawBackground();
        }

        private function _updateDisplay(
            alliesName:String, enemiesName:String,
            alliesRating:int, enemiesRating:int,
            eloPlus:int, eloMinus:int,
            winsPercent:int, battlesCount:int
        ):void
        {
            if (_disposed) return;

            var ratingSize:int = _s(20);
            var nameSize:int = _s(16);
            var smallSize:int = _s(14);

            if (_showTeamNames)
            {
                _alliesNameField.htmlText = _fmt(_truncate(alliesName, 6), nameSize, _alliesNamesColor);
                _enemiesNameField.htmlText = _fmt(_truncate(enemiesName, 6), nameSize, _enemiesNamesColor);
                _enemiesNameField.x = _panelWidth - _enemiesNameField.textWidth - _s(5) - 4;
            }

            _alliesRatingField.htmlText = _fmt(alliesRating > 0 ? String(alliesRating) : " ", ratingSize, _alliesRatingColor);
            _enemiesRatingField.htmlText = _fmt(enemiesRating > 0 ? String(enemiesRating) : " ", ratingSize, _enemiesRatingColor);
            _enemiesRatingField.x = _panelWidth - _enemiesRatingField.textWidth - _s(15) - 4;

            if (_showEloChanges)
            {
                _eloGainField.htmlText = _fmt(eloPlus > 0 ? ("+" + eloPlus) : "", smallSize, _eloGainColor);
                _eloLossField.htmlText = _fmt(eloMinus < 0 ? String(eloMinus) : "", smallSize, _eloLossColor);
                _eloLossField.x = _panelWidth - _eloLossField.textWidth - _s(20) - 4;
            }

            if (_showWinrateAndBattles)
            {
                var statsHtml:String = _buildStatsHtml(battlesCount, winsPercent, smallSize);
                _enemyStatsField.htmlText = statsHtml;
                _enemyStatsField.x = (_panelWidth - _enemyStatsField.textWidth) / 2 - 2;
            }
        }

        private function _buildStatsHtml(battles:int, winrate:int, size:int):String
        {
            if (battles <= 0 && winrate <= 0) return "";
            var parts:Array = [];
            if (battles > 0)
                parts.push('<font face="Tahoma" size="' + size + '" color="' + _getBattlesColor(battles) + '"><b>' + battles + '</b></font>');
            if (winrate > 0)
                parts.push('<font face="Tahoma" size="' + size + '" color="' + _getWinrateColor(winrate) + '"><b>(' + winrate + '%)</b></font>');
            return parts.join(" ");
        }

        private function _getWinrateColor(wr:int):String
        {
            if (wr < 47) return "#FE0E00";
            if (wr < 49) return "#FE7903";
            if (wr < 52) return "#F8F400";
            if (wr < 57) return "#60FF00";
            if (wr < 64) return "#02C9B3";
            return "#D042F3";
        }

        private function _getBattlesColor(b:int):String
        {
            if (b < 50)  return "#AAAAAA";
            if (b < 100) return "#FFFFFF";
            return "#60FF00";
        }

        private function _s(val:int):int { return int(val * _scaleFactor); }

        private function _fmt(text:String, size:int, color:String):String
        {
            return '<font face="Tahoma" size="' + size + '" color="' + color + '"><b>' + text + '</b></font>';
        }

        private function _truncate(name:String, maxLen:int):String
        {
            if (!name || name == "Unknown" || name == " ") return " ";
            if (name.length > maxLen) return name.substr(0, maxLen).toUpperCase();
            return name.toUpperCase();
        }
    }
}
