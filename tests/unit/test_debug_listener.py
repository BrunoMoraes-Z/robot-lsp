from robot_lsp.debug.listener import RobotLspDebugListener


def test_robot_lsp_debug_listener_uses_robot_listener_api_v3():
    assert RobotLspDebugListener.ROBOT_LISTENER_API_VERSION == 3


def test_robot_lsp_debug_listener_stores_runtime_breakpoints(tmp_path):
    source = tmp_path / "suite.robot"
    listener = RobotLspDebugListener.__new__(RobotLspDebugListener)
    listener._breakpoints = {}

    listener._set_breakpoints([{"source": str(source), "line": 3}])

    assert listener._breakpoints[listener._normalize_path(str(source))] == {3}
