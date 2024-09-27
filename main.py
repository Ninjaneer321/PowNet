from datetime import datetime
from pownet.core import (
    SystemInput,
    ModelBuilder,
    SystemRecord,
    OutputProcessor,
    Visualizer,
)
from pownet.modeling import PowerSystemModel
from pownet.data_processor import DataProcessor
from pownet.data_utils import create_init_condition


def main():
    ##### User inputs #####
    to_process_inputs = True
    sim_horizon = 24
    model_name = "RegionAB"
    steps_to_run = 3  # Default is None
    do_plot = True
    do_write_results = True
    #######################

    if to_process_inputs:
        data_processor = DataProcessor(model_name=model_name, year=2016, frequency=50)
        data_processor.execute_data_pipeline()

    inputs = SystemInput(
        model_name=model_name,
        year=2016,
        sim_horizon=sim_horizon,
        spin_reserve_factor=0.15,
        load_shortfall_penalty_factor=1000,
        load_curtail_penalty_factor=1,
        spin_shortfall_penalty_factor=1000,
    )
    inputs.load_and_check_data()

    model_builder = ModelBuilder(inputs)
    init_conditions = create_init_condition(inputs.thermal_units)

    record = SystemRecord(inputs)

    build_times = []
    opt_times = []
    objvals = []

    if steps_to_run is None:
        steps_to_run = 10  # 365 - (sim_horizon // 24 - 1)

    for step_k in range(1, steps_to_run):
        start_time = datetime.now()
        if step_k == 1:
            model = model_builder.build(
                step_k=step_k,
                init_conds=init_conditions,
            )
        else:
            model = model_builder.update(
                step_k=step_k,
                init_conds=init_conditions,
            )
        build_times.append((datetime.now() - start_time).total_seconds())

        power_system_model = PowerSystemModel(model)
        power_system_model.optimize(mipgap=0.001)
        objvals.append(power_system_model.get_objval())
        opt_times.append(power_system_model.get_runtime())

        record.keep(
            runtime=power_system_model.get_runtime(),
            objval=power_system_model.get_objval(),
            solution=power_system_model.get_solution(),
            step_k=step_k,
        )
        init_conditions = record.get_init_conds()

        # Process the results
        output_processor = OutputProcessor(
            year=inputs.year,
            fuelmap=inputs.fuelmap,
            demand=inputs.demand,
        )
        node_var_df = record.get_node_variables()
        output_processor.load_from_dataframe(node_var_df)

        # Visualize the results
        if do_plot:
            visualizer = Visualizer(inputs.model_id)
            if steps_to_run <= 3:
                visualizer.plot_fuelmix_bar(
                    dispatch=output_processor.get_hourly_dispatch(),
                    demand=output_processor.get_hourly_demand(),
                    to_save=False,
                )
            else:
                visualizer = Visualizer(inputs.model_id)
                visualizer.plot_fuelmix_area(
                    dispatch=output_processor.get_daily_dispatch(),
                    demand=output_processor.get_daily_demand(),
                    to_save=False,
                )

        if do_write_results:
            record.write_simulation_results()


if __name__ == "__main__":
    main()
