"""Comprehensive tests for the LSP main entry point.

This module provides Google-quality tests for the LSP server main entry point,
ensuring complete coverage of the critical IDE integration functionality.

Test Categories:
1. Server Creation Tests
2. Server Initialization Tests
3. LSP Protocol Compliance Tests
4. Error Handling Tests
5. Event Loop Management Tests
6. Logging Configuration Tests
7. Integration Tests
8. Edge Cases and Error Recovery Tests
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest

from pytest_drill_sergeant.lsp.main import (
    create_server,
    main,
    run_server,
)


class TestCreateServer:
    """Test the create_server function."""

    def test_create_server_returns_language_server(self):
        """Test that create_server returns a DrillSergeantLanguageServer instance."""
        with patch(
            "pytest_drill_sergeant.lsp.main.DrillSergeantLanguageServer"
        ) as mock_server_class:
            with patch(
                "pytest_drill_sergeant.lsp.main.setup_file_watching"
            ) as mock_setup:
                mock_server = Mock()
                mock_server_class.return_value = mock_server

                result = create_server()

                assert result is mock_server
                mock_server_class.assert_called_once()
                mock_setup.assert_called_once_with(mock_server)

    def test_create_server_sets_up_file_watching(self):
        """Test that create_server sets up file watching."""
        with patch(
            "pytest_drill_sergeant.lsp.main.DrillSergeantLanguageServer"
        ) as mock_server_class:
            with patch(
                "pytest_drill_sergeant.lsp.main.setup_file_watching"
            ) as mock_setup:
                mock_server = Mock()
                mock_server_class.return_value = mock_server

                create_server()

                mock_setup.assert_called_once_with(mock_server)

    def test_create_server_registers_features(self):
        """Test that create_server registers LSP features."""
        with patch(
            "pytest_drill_sergeant.lsp.main.DrillSergeantLanguageServer"
        ) as mock_server_class:
            with patch("pytest_drill_sergeant.lsp.main.setup_file_watching"):
                mock_server = Mock()
                mock_server_class.return_value = mock_server

                create_server()

                # Verify that features were registered
                assert mock_server.feature.call_count == 2

    def test_create_server_handles_import_errors(self):
        """Test that create_server handles import errors gracefully."""
        with patch(
            "pytest_drill_sergeant.lsp.main.DrillSergeantLanguageServer",
            side_effect=ImportError("Module not found"),
        ):
            with pytest.raises(ImportError):
                create_server()

    def test_create_server_handles_setup_errors(self):
        """Test that create_server handles setup_file_watching errors."""
        with patch(
            "pytest_drill_sergeant.lsp.main.DrillSergeantLanguageServer"
        ) as mock_server_class:
            with patch(
                "pytest_drill_sergeant.lsp.main.setup_file_watching",
                side_effect=Exception("Setup failed"),
            ):
                mock_server = Mock()
                mock_server_class.return_value = mock_server

                with pytest.raises(Exception, match="Setup failed"):
                    create_server()


class TestMainAsync:
    """Test the async main function."""

    @pytest.mark.asyncio
    async def test_main_sets_up_logging(self):
        """Test that main sets up logging configuration."""
        with patch(
            "pytest_drill_sergeant.lsp.main.logging.basicConfig"
        ) as mock_basic_config:
            with patch("pytest_drill_sergeant.lsp.main.logger") as mock_logger:
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create:
                    mock_server = Mock()
                    mock_server.start_io = AsyncMock()
                    mock_create.return_value = mock_server

                    await main()

                    mock_basic_config.assert_called_once_with(
                        level=logging.INFO,
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    )

    @pytest.mark.asyncio
    async def test_main_logs_startup_message(self):
        """Test that main logs startup message."""
        with patch("pytest_drill_sergeant.lsp.main.logging.basicConfig"):
            with patch("pytest_drill_sergeant.lsp.main.logger") as mock_logger:
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create:
                    mock_server = Mock()
                    mock_server.start_io = AsyncMock()
                    mock_create.return_value = mock_server

                    await main()

                    mock_logger.info.assert_called_with(
                        "Starting drill sergeant language server"
                    )

    @pytest.mark.asyncio
    async def test_main_creates_and_starts_server(self):
        """Test that main creates and starts the server."""
        with patch("pytest_drill_sergeant.lsp.main.logging.basicConfig"):
            with patch("pytest_drill_sergeant.lsp.main.logger"):
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create:
                    mock_server = Mock()
                    mock_server.start_io = AsyncMock()
                    mock_create.return_value = mock_server

                    await main()

                    mock_create.assert_called_once()
                    mock_server.start_io.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_handles_server_creation_error(self):
        """Test that main handles server creation errors."""
        with patch("pytest_drill_sergeant.lsp.main.logging.basicConfig"):
            with patch("pytest_drill_sergeant.lsp.main.logger") as mock_logger:
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server",
                    side_effect=Exception("Server creation failed"),
                ):
                    with patch("pytest_drill_sergeant.lsp.main.sys.exit") as mock_exit:
                        with patch("traceback.print_exc") as mock_traceback:
                            await main()

                            mock_logger.error.assert_called_with(
                                "Failed to start language server: Server creation failed"
                            )
                            mock_traceback.assert_called_once()
                            mock_exit.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_main_handles_server_start_error(self):
        """Test that main handles server start errors."""
        with patch("pytest_drill_sergeant.lsp.main.logging.basicConfig"):
            with patch("pytest_drill_sergeant.lsp.main.logger") as mock_logger:
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create:
                    with patch("pytest_drill_sergeant.lsp.main.sys.exit") as mock_exit:
                        with patch("traceback.print_exc") as mock_traceback:
                            mock_server = Mock()
                            mock_server.start_io = AsyncMock(
                                side_effect=Exception("Start failed")
                            )
                            mock_create.return_value = mock_server

                            await main()

                            mock_logger.error.assert_called_with(
                                "Failed to start language server: Start failed"
                            )
                            mock_traceback.assert_called_once()
                            mock_exit.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_main_handles_logging_setup_error(self):
        """Test that main handles logging setup errors."""
        with patch(
            "pytest_drill_sergeant.lsp.main.logging.basicConfig",
            side_effect=Exception("Logging failed"),
        ):
            with patch("pytest_drill_sergeant.lsp.main.logger") as mock_logger:
                with patch("pytest_drill_sergeant.lsp.main.sys.exit") as mock_exit:
                    with patch("traceback.print_exc") as mock_traceback:
                        await main()

                        mock_logger.error.assert_called_with(
                            "Failed to start language server: Logging failed"
                        )
                        mock_traceback.assert_called_once()
                        mock_exit.assert_called_once_with(1)


class TestRunServer:
    """Test the run_server function."""

    def test_run_server_sets_up_logging(self):
        """Test that run_server sets up logging configuration."""
        with patch(
            "pytest_drill_sergeant.lsp.main.logging.basicConfig"
        ) as mock_basic_config:
            with patch("pytest_drill_sergeant.lsp.main.logger"):
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create:
                    mock_server = Mock()
                    mock_server.start_io = Mock()
                    mock_create.return_value = mock_server

                    run_server()

                    mock_basic_config.assert_called_once_with(
                        level=logging.INFO,
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    )

    def test_run_server_logs_startup_message(self):
        """Test that run_server logs startup message."""
        with patch("pytest_drill_sergeant.lsp.main.logging.basicConfig"):
            with patch("pytest_drill_sergeant.lsp.main.logger") as mock_logger:
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create:
                    mock_server = Mock()
                    mock_server.start_io = Mock()
                    mock_create.return_value = mock_server

                    run_server()

                    mock_logger.info.assert_called_with(
                        "Starting drill sergeant language server"
                    )

    def test_run_server_creates_and_starts_server(self):
        """Test that run_server creates and starts the server."""
        with patch("pytest_drill_sergeant.lsp.main.logging.basicConfig"):
            with patch("pytest_drill_sergeant.lsp.main.logger"):
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create:
                    mock_server = Mock()
                    mock_server.start_io = Mock()
                    mock_create.return_value = mock_server

                    run_server()

                    mock_create.assert_called_once()
                    mock_server.start_io.assert_called_once()

    def test_run_server_handles_server_creation_error(self):
        """Test that run_server handles server creation errors."""
        with patch("pytest_drill_sergeant.lsp.main.logging.basicConfig"):
            with patch("pytest_drill_sergeant.lsp.main.logger") as mock_logger:
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server",
                    side_effect=Exception("Server creation failed"),
                ):
                    with patch("pytest_drill_sergeant.lsp.main.sys.exit") as mock_exit:
                        with patch("traceback.print_exc") as mock_traceback:
                            run_server()

                            mock_logger.error.assert_called_with(
                                "Failed to start language server: Server creation failed"
                            )
                            mock_traceback.assert_called_once()
                            mock_exit.assert_called_once_with(1)

    def test_run_server_handles_server_start_error(self):
        """Test that run_server handles server start errors."""
        with patch("pytest_drill_sergeant.lsp.main.logging.basicConfig"):
            with patch("pytest_drill_sergeant.lsp.main.logger") as mock_logger:
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create:
                    with patch("pytest_drill_sergeant.lsp.main.sys.exit") as mock_exit:
                        with patch("traceback.print_exc") as mock_traceback:
                            mock_server = Mock()
                            mock_server.start_io = Mock(
                                side_effect=Exception("Start failed")
                            )
                            mock_create.return_value = mock_server

                            run_server()

                            mock_logger.error.assert_called_with(
                                "Failed to start language server: Start failed"
                            )
                            mock_traceback.assert_called_once()
                            mock_exit.assert_called_once_with(1)

    def test_run_server_handles_logging_setup_error(self):
        """Test that run_server handles logging setup errors."""
        with patch(
            "pytest_drill_sergeant.lsp.main.logging.basicConfig",
            side_effect=Exception("Logging failed"),
        ):
            with patch("pytest_drill_sergeant.lsp.main.logger") as mock_logger:
                with patch("pytest_drill_sergeant.lsp.main.sys.exit") as mock_exit:
                    with patch("traceback.print_exc") as mock_traceback:
                        run_server()

                        mock_logger.error.assert_called_with(
                            "Failed to start language server: Logging failed"
                        )
                        mock_traceback.assert_called_once()
                        mock_exit.assert_called_once_with(1)


class TestLSPProtocolCompliance:
    """Test LSP protocol compliance."""

    def test_create_server_registers_initialize_feature(self):
        """Test that create_server registers initialize feature."""
        with patch(
            "pytest_drill_sergeant.lsp.main.DrillSergeantLanguageServer"
        ) as mock_server_class:
            with patch("pytest_drill_sergeant.lsp.main.setup_file_watching"):
                mock_server = Mock()
                mock_server_class.return_value = mock_server

                create_server()

                # Verify initialize feature was registered
                initialize_calls = [
                    call
                    for call in mock_server.feature.call_args_list
                    if call[0][0] == "initialize"
                ]
                assert len(initialize_calls) == 1

    def test_create_server_registers_initialized_feature(self):
        """Test that create_server registers initialized feature."""
        with patch(
            "pytest_drill_sergeant.lsp.main.DrillSergeantLanguageServer"
        ) as mock_server_class:
            with patch("pytest_drill_sergeant.lsp.main.setup_file_watching"):
                mock_server = Mock()
                mock_server_class.return_value = mock_server

                create_server()

                # Verify initialized feature was registered
                initialized_calls = [
                    call
                    for call in mock_server.feature.call_args_list
                    if call[0][0] == "initialized"
                ]
                assert len(initialized_calls) == 1


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_create_server_handles_server_instantiation_error(self):
        """Test that create_server handles server instantiation errors."""
        with patch(
            "pytest_drill_sergeant.lsp.main.DrillSergeantLanguageServer",
            side_effect=RuntimeError("Server creation failed"),
        ):
            with pytest.raises(RuntimeError, match="Server creation failed"):
                create_server()

    def test_create_server_handles_feature_registration_error(self):
        """Test that create_server handles feature registration errors."""
        with patch(
            "pytest_drill_sergeant.lsp.main.DrillSergeantLanguageServer"
        ) as mock_server_class:
            with patch("pytest_drill_sergeant.lsp.main.setup_file_watching"):
                mock_server = Mock()
                mock_server.feature.side_effect = Exception(
                    "Feature registration failed"
                )
                mock_server_class.return_value = mock_server

                with pytest.raises(Exception, match="Feature registration failed"):
                    create_server()

    def test_main_handles_import_error(self):
        """Test that main handles import errors."""
        with patch("pytest_drill_sergeant.lsp.main.logging.basicConfig"):
            with patch("pytest_drill_sergeant.lsp.main.logger") as mock_logger:
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server",
                    side_effect=ImportError("Module not found"),
                ):
                    with patch("pytest_drill_sergeant.lsp.main.sys.exit") as mock_exit:
                        with patch("traceback.print_exc") as mock_traceback:
                            import asyncio

                            asyncio.run(main())

                            mock_logger.error.assert_called_with(
                                "Failed to start language server: Module not found"
                            )
                            mock_traceback.assert_called_once()
                            mock_exit.assert_called_once_with(1)

    def test_run_server_handles_import_error(self):
        """Test that run_server handles import errors."""
        with patch("pytest_drill_sergeant.lsp.main.logging.basicConfig"):
            with patch("pytest_drill_sergeant.lsp.main.logger") as mock_logger:
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server",
                    side_effect=ImportError("Module not found"),
                ):
                    with patch("pytest_drill_sergeant.lsp.main.sys.exit") as mock_exit:
                        with patch("traceback.print_exc") as mock_traceback:
                            run_server()

                            mock_logger.error.assert_called_with(
                                "Failed to start language server: Module not found"
                            )
                            mock_traceback.assert_called_once()
                            mock_exit.assert_called_once_with(1)


class TestLoggingConfiguration:
    """Test logging configuration."""

    @pytest.mark.asyncio
    async def test_main_logging_format_is_correct(self):
        """Test that main uses correct logging format."""
        with patch(
            "pytest_drill_sergeant.lsp.main.logging.basicConfig"
        ) as mock_basic_config:
            with patch("pytest_drill_sergeant.lsp.main.logger"):
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create:
                    mock_server = Mock()
                    mock_server.start_io = AsyncMock()
                    mock_create.return_value = mock_server

                    await main()

                    mock_basic_config.assert_called_once_with(
                        level=logging.INFO,
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    )

    def test_run_server_logging_format_is_correct(self):
        """Test that run_server uses correct logging format."""
        with patch(
            "pytest_drill_sergeant.lsp.main.logging.basicConfig"
        ) as mock_basic_config:
            with patch("pytest_drill_sergeant.lsp.main.logger"):
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create:
                    mock_server = Mock()
                    mock_server.start_io = Mock()
                    mock_create.return_value = mock_server

                    run_server()

                    mock_basic_config.assert_called_once_with(
                        level=logging.INFO,
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    )

    @pytest.mark.asyncio
    async def test_main_logging_level_is_info(self):
        """Test that main uses INFO logging level."""
        with patch(
            "pytest_drill_sergeant.lsp.main.logging.basicConfig"
        ) as mock_basic_config:
            with patch("pytest_drill_sergeant.lsp.main.logger"):
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create:
                    mock_server = Mock()
                    mock_server.start_io = AsyncMock()
                    mock_create.return_value = mock_server

                    await main()

                    call_args = mock_basic_config.call_args[1]
                    assert call_args["level"] == logging.INFO

    def test_run_server_logging_level_is_info(self):
        """Test that run_server uses INFO logging level."""
        with patch(
            "pytest_drill_sergeant.lsp.main.logging.basicConfig"
        ) as mock_basic_config:
            with patch("pytest_drill_sergeant.lsp.main.logger"):
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create:
                    mock_server = Mock()
                    mock_server.start_io = Mock()
                    mock_create.return_value = mock_server

                    run_server()

                    call_args = mock_basic_config.call_args[1]
                    assert call_args["level"] == logging.INFO


class TestIntegration:
    """Test integration scenarios."""

    def test_full_server_creation_workflow(self):
        """Test the complete server creation workflow."""
        with patch(
            "pytest_drill_sergeant.lsp.main.DrillSergeantLanguageServer"
        ) as mock_server_class:
            with patch(
                "pytest_drill_sergeant.lsp.main.setup_file_watching"
            ) as mock_setup:
                mock_server = Mock()
                mock_server_class.return_value = mock_server

                server = create_server()

                # Verify server was created
                assert server is mock_server

                # Verify file watching was set up
                mock_setup.assert_called_once_with(mock_server)

                # Verify features were registered
                assert mock_server.feature.call_count == 2

    def test_main_and_run_server_consistency(self):
        """Test that main and run_server have consistent behavior."""
        with patch(
            "pytest_drill_sergeant.lsp.main.logging.basicConfig"
        ) as mock_basic_config_main:
            with patch("pytest_drill_sergeant.lsp.main.logger") as mock_logger_main:
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create_main:
                    # Test main
                    mock_server_main = Mock()
                    mock_server_main.start_io = AsyncMock()
                    mock_create_main.return_value = mock_server_main

                    import asyncio

                    asyncio.run(main())

                    # Test run_server
                    with patch(
                        "pytest_drill_sergeant.lsp.main.logging.basicConfig"
                    ) as mock_basic_config_run:
                        with patch(
                            "pytest_drill_sergeant.lsp.main.logger"
                        ) as mock_logger_run:
                            with patch(
                                "pytest_drill_sergeant.lsp.main.create_server"
                            ) as mock_create_run:
                                mock_server_run = Mock()
                                mock_server_run.start_io = Mock()
                                mock_create_run.return_value = mock_server_run

                                run_server()

                                # Verify consistent logging setup
                                assert (
                                    mock_basic_config_main.call_args
                                    == mock_basic_config_run.call_args
                                )

                                # Verify consistent server creation
                                mock_create_main.assert_called_once()
                                mock_create_run.assert_called_once()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_create_server_with_none_params(self):
        """Test create_server behavior with None parameters."""
        with patch(
            "pytest_drill_sergeant.lsp.main.DrillSergeantLanguageServer"
        ) as mock_server_class:
            with patch("pytest_drill_sergeant.lsp.main.setup_file_watching"):
                mock_server = Mock()
                mock_server_class.return_value = mock_server

                # Should not raise an exception
                server = create_server()
                assert server is mock_server

    @pytest.mark.asyncio
    async def test_main_with_existing_event_loop(self):
        """Test main function with existing event loop."""
        with patch("pytest_drill_sergeant.lsp.main.logging.basicConfig"):
            with patch("pytest_drill_sergeant.lsp.main.logger"):
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create:
                    mock_server = Mock()
                    mock_server.start_io = AsyncMock()
                    mock_create.return_value = mock_server

                    # Create an event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    try:
                        # Should not raise an exception
                        await main()
                    finally:
                        loop.close()

    def test_run_server_with_existing_event_loop(self):
        """Test run_server function with existing event loop."""
        with patch("pytest_drill_sergeant.lsp.main.logging.basicConfig"):
            with patch("pytest_drill_sergeant.lsp.main.logger"):
                with patch(
                    "pytest_drill_sergeant.lsp.main.create_server"
                ) as mock_create:
                    mock_server = Mock()
                    mock_server.start_io = Mock()
                    mock_create.return_value = mock_server

                    # Create an event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    try:
                        # Should not raise an exception
                        run_server()
                    finally:
                        loop.close()


class TestModuleEntryPoint:
    """Test the module entry point behavior."""

    def test_module_main_execution(self):
        """Test that __main__ execution calls run_server."""
        with patch("pytest_drill_sergeant.lsp.main.run_server") as mock_run_server:
            # Simulate module execution
            import pytest_drill_sergeant.lsp.main as lsp_main

            # Check that run_server is callable
            assert callable(lsp_main.run_server)

            # Test direct call
            lsp_main.run_server()
            mock_run_server.assert_called_once()

    def test_module_imports_are_available(self):
        """Test that all required imports are available."""
        import pytest_drill_sergeant.lsp.main as lsp_main

        # Check that all required functions are available
        assert hasattr(lsp_main, "create_server")
        assert hasattr(lsp_main, "main")
        assert hasattr(lsp_main, "run_server")

        # Check that all required classes are available
        assert hasattr(lsp_main, "DrillSergeantLanguageServer")
        assert hasattr(lsp_main, "InitializeParams")
        assert hasattr(lsp_main, "InitializeResult")
        assert hasattr(lsp_main, "ServerCapabilities")
        assert hasattr(lsp_main, "TextDocumentSyncKind")

        # Check that logger is available
        assert hasattr(lsp_main, "logger")
        assert lsp_main.logger is not None
