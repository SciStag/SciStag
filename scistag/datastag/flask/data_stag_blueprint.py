from flask import Blueprint, request, jsonify, current_app
from scistag.datastag.data_stag_command_handler import DataStagCommandHandler


class DataStagService(Blueprint):
    """
    Provides a blueprint to access a DataStag vault remotely via HTTP
    """

    def __init__(self):
        """
        Initializer
        """
        super().__init__(
            "DataStag",
            __name__,
            template_folder="./templates",
            static_folder="./static",
        )
        self.command_handler = DataStagCommandHandler(local=True)
        "The wrapper from http commands to vault commands"


data_stag_service = DataStagService()


@data_stag_service.route("/run", methods=["POST"])
def handle_run():
    """
    Execution function. Converts all commands provided as a JSON object or list
    of JSON object to local Vault commands and returns their data
    """
    json_data = request.get_json()
    if json_data is not None:
        result = data_stag_service.command_handler.handle_command_data(json_data)
        return jsonify(result)
    current_app.logger.error("No data provided to DataStag call")
    return jsonify({})
