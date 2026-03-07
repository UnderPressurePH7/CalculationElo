package com.github.under.calculationelo
{
    import flash.events.Event;
    import net.wg.gui.battle.components.BattleUIDisplayable;
    import net.wg.gui.battle.views.BaseBattlePage;

    public class EloBattleDisplayable extends BattleUIDisplayable
    {
        public var battlePage:BaseBattlePage;
        public var componentName:String;

        public function EloBattleDisplayable()
        {
            super();
        }

        public function initBattle():void
        {
            if (!this.battlePage.contains(this))
            {
                this.battlePage.addChild(this);
            }
            if (!this.battlePage.isFlashComponentRegisteredS(this.componentName))
            {
                this.battlePage.registerFlashComponentS(this, this.componentName);
            }
        }

        public function finiBattle():void
        {
            if (this.battlePage.isFlashComponentRegisteredS(this.componentName))
            {
                this.battlePage.unregisterFlashComponentS(this.componentName);
            }
            if (this.battlePage.contains(this))
            {
                this.battlePage.removeChild(this);
            }
        }

        override protected function onPopulate():void
        {
            super.onPopulate();
            this.battlePage.addEventListener(Event.RESIZE, _handleResize);
        }

        override protected function onDispose():void
        {
            this.battlePage.removeEventListener(Event.RESIZE, _handleResize);
            this.finiBattle();
            super.onDispose();
        }

        private function _handleResize(e:Event):void
        {
            this.onResized();
        }

        protected function onResized():void
        {
        }
    }
}
