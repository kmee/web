/** @odoo-module **/

const {useEffect, Component, onWillStart, useRef} = owl;
import {loadJS} from "@web/core/assets";
import {registry} from "@web/core/registry";

export class JSONGraphWidget extends Component {
    setup() {
        this.chart = null;
        this.canvasRef = useRef("canvas");
        const rawData = this.props.record.data[this.props.name];
        this.data = rawData ? JSON.parse(rawData) : null;

        super.setup();
        onWillStart(() => loadJS("/web/static/lib/Chart/Chart.js"));
        useEffect(() => {
            this.renderChart();
            return () => {
                if (this.chart) {
                    this.chart.destroy();
                }
            };
        });
    }
    renderChart() {
        if (this.chart) {
            this.chart.destroy();
        }
        if (!this.data || !this.canvasRef.el) {
            return;
        }
        // eslint-disable-next-line no-undef
        this.chart = new Chart(this.canvasRef.el, this.data);
        return this.chart;
    }
}

export const jsonGraphWidget = {
    component: JSONGraphWidget,
};

JSONGraphWidget.template = "web_widget_json_graph.JSONGraph";
registry.category("fields").add("json_graph", jsonGraphWidget);
