package com.github.under.calculationelo
{
    public class EloPanelInjector extends AbstractComponentInjector
    {
        public function EloPanelInjector()
        {
            super();
        }

        override protected function onPopulate():void
        {
            this.autoDestroy = false; 
            this.componentName = "EloPanelMain";
            this.componentUI = EloPanelComponent; // Ваш основний клас інтерфейсу

            super.onPopulate();
        }
    }
}
