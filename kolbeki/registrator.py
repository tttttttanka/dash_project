from kolbeki.parametry_kollbeki import register_parameter_callbacks
from kolbeki.raschety_kollbeki import register_calculation_callbacks
from kolbeki.serii_kollbeki import register_series_table_callbacks
from kolbeki.grafiki_kollbeki import register_plot_callbacks
from kolbeki.istoriya_kollbeki import register_history_callbacks


def register_callbacks(app, base_dir):
    # Регистрация колбэков в нужном порядке.
    register_parameter_callbacks(app)
    register_calculation_callbacks(app, base_dir)
    register_series_table_callbacks(app)
    register_plot_callbacks(app, base_dir)
    register_history_callbacks(app, base_dir)

