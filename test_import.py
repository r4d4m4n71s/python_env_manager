from env_manager import EnvManager, Environment, GlobalState, read_toml

print("Import successful!")
print(f"EnvManager: {EnvManager}")
print(f"Environment: {Environment}")
print(f"GlobalState: {GlobalState}")
print(f"read_toml: {read_toml}")

# Test GlobalState
state = GlobalState("TestApp")
state["test_key"] = "test_value"
print(f"GlobalState instance: {state}")

# Test read_toml
data = read_toml()
print(f"TOML data: {data}")