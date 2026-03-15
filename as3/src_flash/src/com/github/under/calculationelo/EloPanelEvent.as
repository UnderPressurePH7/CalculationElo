package com.github.under.calculationelo
{
    import flash.events.Event;

    public class EloPanelEvent extends Event
    {
        public static const OFFSET_CHANGED:String = "EloPanelEvent.OFFSET_CHANGED";

        private var _data:* = null;

        public function EloPanelEvent(type:String, data:* = null, bubbles:Boolean = true, cancelable:Boolean = false)
        {
            super(type, bubbles, cancelable);
            _data = data;
        }

        override public function clone():Event
        {
            return new EloPanelEvent(type, _data, bubbles, cancelable);
        }

        public function get data():*
        {
            return _data;
        }
    }
}
