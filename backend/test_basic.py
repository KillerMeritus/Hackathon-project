#!/usr/bin/env python3
"""
Basic Test Script - Verifies the core components work correctly
Run this to make sure everything is set up properly before using API keys.
"""
import sys
import os

# Fix for Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")

    try:
        from app.core.models import AgentConfig, WorkflowConfig, YAMLConfig, ExecutionResult
        print("  ✓ Core models imported")
    except Exception as e:
        print(f"  ✗ Core models failed: {e}")
        return False

    try:
        from app.core.yaml_parser import load_and_parse, validate_yaml
        print("  ✓ YAML parser imported")
    except Exception as e:
        print(f"  ✗ YAML parser failed: {e}")
        return False

    try:
        from app.core.exceptions import YAMLParseError, ValidationError
        print("  ✓ Exceptions imported")
    except Exception as e:
        print(f"  ✗ Exceptions failed: {e}")
        return False

    try:
        from app.engine.memory import SharedMemory
        from app.engine.context import ContextBuilder
        print("  ✓ Memory and Context imported")
    except Exception as e:
        print(f"  ✗ Memory/Context failed: {e}")
        return False

    try:
        from app.engine.executors import SequentialExecutor, ParallelExecutor
        print("  ✓ Executors imported")
    except Exception as e:
        print(f"  ✗ Executors failed: {e}")
        return False

    try:
        from app.agents.base import Agent
        from app.agents.factory import create_agent
        print("  ✓ Agent system imported")
    except Exception as e:
        print(f"  ✗ Agent system failed: {e}")
        return False

    try:
        from app.llm.base import BaseLLMProvider
        from app.llm.factory import get_llm_provider, PROVIDER_REGISTRY
        print("  ✓ LLM providers imported")
    except Exception as e:
        print(f"  ✗ LLM providers failed: {e}")
        return False

    try:
        from app.tools.registry import get_tool, list_tools
        print("  ✓ Tools imported")
    except Exception as e:
        print(f"  ✗ Tools failed: {e}")
        return False

    return True


def test_yaml_parsing():
    """Test YAML parsing"""
    print("\nTesting YAML parsing...")

    from app.core.yaml_parser import load_and_parse, validate_yaml

    # Test sequential workflow
    try:
        config = load_and_parse("examples/sequential.yaml")
        print(f"  ✓ Sequential YAML parsed: {len(config.agents)} agents")
    except Exception as e:
        print(f"  ✗ Sequential YAML failed: {e}")
        return False

    # Test parallel workflow
    try:
        config = load_and_parse("examples/parallel.yaml")
        print(f"  ✓ Parallel YAML parsed: {len(config.agents)} agents")
    except Exception as e:
        print(f"  ✗ Parallel YAML failed: {e}")
        return False

    return True


def test_memory():
    """Test shared memory"""
    print("\nTesting shared memory...")

    from app.engine.memory import SharedMemory

    try:
        memory = SharedMemory("test-workflow")
        memory.store_output("agent1", "Test output 1")
        memory.store_output("agent2", "Test output 2")

        assert memory.get_output("agent1") == "Test output 1"
        assert memory.get_output("agent2") == "Test output 2"
        assert len(memory.get_all_outputs()) == 2

        print("  ✓ Memory storage works")
    except Exception as e:
        print(f"  ✗ Memory storage failed: {e}")
        return False

    try:
        memory.save_to_file("test-memory.json")
        print("  ✓ Memory save works")

        new_memory = SharedMemory("test-workflow")
        new_memory.load_from_file("test-memory.json")
        assert new_memory.get_output("agent1") == "Test output 1"
        print("  ✓ Memory load works")

        # Cleanup
        import os
        os.remove("memory/test-memory.json")
    except Exception as e:
        print(f"  ✗ Memory persistence failed: {e}")
        return False

    return True


def test_context_builder():
    """Test context builder"""
    print("\nTesting context builder...")

    from app.engine.memory import SharedMemory
    from app.engine.context import ContextBuilder
    from app.core.models import AgentConfig

    try:
        memory = SharedMemory("test-context")
        memory.store_output("researcher", "Research findings...")

        builder = ContextBuilder(memory)

        agent_config = AgentConfig(
            id="writer",
            role="Writer",
            goal="Write content"
        )

        context = builder.build_sequential_context(
            query="Test query",
            current_agent=agent_config,
            executed_agents=["researcher"]
        )

        assert context["query"] == "Test query"
        assert "researcher" in context["previous_outputs"]
        assert context["current_agent"]["id"] == "writer"

        print("  ✓ Context builder works")
        return True
    except Exception as e:
        print(f"  ✗ Context builder failed: {e}")
        return False


def test_tools():
    """Test tools system"""
    print("\nTesting tools...")

    from app.tools.registry import get_tool, list_tools

    try:
        tools = list_tools()
        print(f"  ✓ Available tools: {tools}")

        python_tool = get_tool("python")
        if python_tool:
            print(f"  ✓ Python tool found: {python_tool.description}")
        else:
            print("  ⚠ Python tool not found (optional)")

        return True
    except Exception as e:
        print(f"  ✗ Tools failed: {e}")
        return False


def test_llm_registry():
    """Test LLM provider registry"""
    print("\nTesting LLM registry...")

    from app.llm.factory import PROVIDER_REGISTRY

    try:
        providers = list(set(PROVIDER_REGISTRY.keys()))
        print(f"  ✓ Registered providers: {providers}")
        return True
    except Exception as e:
        print(f"  ✗ LLM registry failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("YAML Multi-Agent Orchestration Engine - Basic Tests")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("YAML Parsing", test_yaml_parsing()))
    results.append(("Memory", test_memory()))
    results.append(("Context Builder", test_context_builder()))
    results.append(("Tools", test_tools()))
    results.append(("LLM Registry", test_llm_registry()))

    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)

    passed = 0
    failed = 0

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"Total: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n✓ All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("  1. Add your API keys to .env file")
        print("  2. Run: python run.py examples/sequential.yaml --query 'Your question'")
        print("  3. Or start the API: python run.py --server")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
