package com.github.under.calculationelo
{
    import net.wg.data.constants.generated.LAYER_NAMES;
    import net.wg.gui.battle.views.BaseBattlePage;
    import net.wg.gui.components.containers.MainViewContainer;
    import net.wg.infrastructure.base.AbstractView;
    import net.wg.infrastructure.interfaces.ISimpleManagedContainer;

    public class EloPanelInjector extends AbstractView
    {
        private static const COMPONENT_NAME:String = "EloPanelMain";

        private static var _activeComponent:EloPanelComponent = null;

        public var py_onDragEnd:Function = null;

        public function EloPanelInjector()
        {
            super();
        }

        override protected function onPopulate():void
        {
            super.onPopulate();

            if (_activeComponent != null)
            {
                return;
            }

            var mainViewContainer:MainViewContainer = MainViewContainer(
                App.containerMgr.getContainer(
                    LAYER_NAMES.LAYER_ORDER.indexOf(LAYER_NAMES.VIEWS)
                )
            );

            if (mainViewContainer == null)
            {
                return;
            }

            var view:BaseBattlePage = null;
            var idx:int = 0;
            while (idx < mainViewContainer.numChildren)
            {
                view = mainViewContainer.getChildAt(idx) as BaseBattlePage;
                if (view) break;
                idx++;
            }

            if (view)
            {
                var component:EloPanelComponent = new EloPanelComponent();
                component.componentName = COMPONENT_NAME;
                component.battlePage = view;
                component.initBattle();
                component.addEventListener(EloPanelEvent.OFFSET_CHANGED, _onOffsetChanged);
                _activeComponent = component;
            }

            var topView:ISimpleManagedContainer = mainViewContainer.getTopmostView();
            if (topView != null)
            {
                mainViewContainer.setFocusedView(topView);
            }
        }

        override protected function onDispose():void
        {
            _destroyComponent();
            py_onDragEnd = null;
            super.onDispose();
        }

        private function _destroyComponent():void
        {
            if (_activeComponent)
            {
                _activeComponent.removeEventListener(EloPanelEvent.OFFSET_CHANGED, _onOffsetChanged);
                _activeComponent.cleanup();
                _activeComponent = null;
            }
        }

        private function _onOffsetChanged(event:EloPanelEvent):void
        {
            if (py_onDragEnd != null)
            {
                py_onDragEnd(event.data);
            }
        }
    }
}
