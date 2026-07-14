from controllers.model_repository import ModelRepository

repo = ModelRepository()
active_model = repo.get_active_model_id()
print("Active Model ID:", active_model)
contract = repo.get_generation_parameters(active_model)
print("Contract:", contract)
