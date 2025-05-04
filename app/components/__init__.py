"""
Inicialización del paquete de componentes.
Exporta los componentes principales de la aplicación.
"""

# Componentes UI
from app.components.ui.cards import stat_card, info_card, party_card, scrutiny_card, custom_card
from app.components.ui.metrics import render_metrics_cards, metric_row
from app.components.ui.charts import create_vote_distribution_chart, create_party_pie_chart, create_bar_chart, render_chart
from app.components.ui.tables import display_results_table, display_comparison_table, display_party_color_table
from app.components.ui.containers import section_container, tabs_container, grid_container, info_container
from app.components.ui.layout import header, footer, sidebar_filters, two_column_layout

# Componentes funcionales
from app.components.functional.map_generator import (
    create_department_choropleth,
    create_municipality_map
)

# Dashboards completos
from app.components.dashboards.national_dashboard import display_national_dashboard
from app.components.dashboards.department_dashboard import display_department_dashboard
from app.components.dashboards.comparison_dashboard import display_comparison_dashboard

# Dashboards
from app.components.dashboards.map_dashboard import display_map_dashboard

__all__ = [
    'display_map_dashboard',
    'display_national_dashboard',
    'display_department_dashboard',
    'create_department_choropleth',
    'create_municipality_map'
] 