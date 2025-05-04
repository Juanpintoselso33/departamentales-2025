"""
Componentes de UI reutilizables.
Contiene elementos visuales puros que no dependen directamente de la lógica de negocio.
"""

# Componentes de tarjetas y contenedores
from app.components.ui.cards import stat_card, info_card, party_card, scrutiny_card, custom_card
from app.components.ui.containers import section_container, tabs_container, grid_container, info_container

# Componentes de visualización
from app.components.ui.charts import (
    create_vote_distribution_chart, create_party_pie_chart, 
    create_bar_chart, create_comparison_chart, render_chart
)
from app.components.ui.tables import (
    display_dataframe, display_results_table, 
    display_comparison_table, display_party_color_table
)

# Componentes de métricas
from app.components.ui.metrics import render_metrics_cards, metric_row

# Componentes de layout
from app.components.ui.layout import header, footer, sidebar_filters, two_column_layout, conditional_display 