"""
Django management command to run the MCP server.

Usage:
    python manage.py mcp_server --user=<username>
"""
import os
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

# Allow Django ORM calls in async context (needed for FastMCP)
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'

logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = 'Run the MCP (Model Context Protocol) server'
    requires_system_checks = []  # Disable system checks to keep stdio clean for JSON-RPC

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            required=True,
            help='Username for MCP context (e.g., admin, maria)'
        )

    def handle(self, *args, **options):
        logger.info('=' * 80)
        logger.info('MCP Server: HANDLE METHOD STARTED')
        logger.info('=' * 80)
        
        username = options['user']
        logger.info(f'MCP Server: Username from options: {username}')
        
        # Get user from database
        logger.info('MCP Server: Attempting to fetch user from database...')
        try:
            user = User.objects.get(username=username)
            logger.info(f'MCP Server: ✓ User found - username={username}, id={user.id}, email={user.email}')
            # DO NOT write to stdout - it interferes with JSON-RPC protocol
            # self.stdout.write(self.style.SUCCESS(f'MCP Server: User context set to {username}'))
        except User.DoesNotExist:
            logger.error(f'MCP Server: ✗ User "{username}" not found in database')
            self.stderr.write(self.style.ERROR(f'User "{username}" not found in database'))
            self.stderr.write(self.style.WARNING('Available users:'))
            for u in User.objects.all()[:10]:
                self.stderr.write(f'  - {u.username}')
            return
        except Exception as e:
            logger.error(f'MCP Server: ✗ Unexpected error fetching user: {e}', exc_info=True)
            raise
        
        # Set user context
        logger.info('MCP Server: Importing set_current_user function...')
        from mcp_integration.context import set_current_user
        logger.info('MCP Server: ✓ Import successful')
        
        logger.info(f'MCP Server: Setting current user context to {user.username}...')
        set_current_user(user)
        logger.info(f'MCP Server: ✓ User context set successfully')
        
        # Initialize and run FastMCP server
        logger.info('MCP Server: Importing initialize_mcp function...')
        from mcp_integration.tools import initialize_mcp
        logger.info('MCP Server: ✓ Import successful')
        
        logger.info('MCP Server: Calling initialize_mcp()...')
        mcp = initialize_mcp()
        logger.info('MCP Server: ✓ initialize_mcp() returned successfully')
        
        # DO NOT write to stdout - it interferes with JSON-RPC protocol
        # self.stdout.write(self.style.SUCCESS('MCP Server: Starting FastMCP server...'))
        logger.info('MCP Server: FastMCP initialized with 16 tools')
        
        # Run the server
        logger.info('MCP Server: Preparing to run FastMCP server...')
        
        # CRITICAL: Disable console logging to prevent interference with stdio JSON-RPC protocol
        logger.info('MCP Server: Disabling console handler to prevent stdio interference...')
        import logging as logging_module
        root_logger = logging_module.getLogger()
        console_handlers = [h for h in root_logger.handlers if isinstance(h, logging_module.StreamHandler) and not isinstance(h, logging_module.FileHandler)]
        for handler in console_handlers:
            root_logger.removeHandler(handler)
            logger.info(f'MCP Server: Removed console handler: {handler}')
        
        # Also remove console handlers from all loggers
        for logger_name in ['django', 'mcp_integration', 'methodology', 'accounts']:
            app_logger = logging_module.getLogger(logger_name)
            console_handlers = [h for h in app_logger.handlers if isinstance(h, logging_module.StreamHandler) and not isinstance(h, logging_module.FileHandler)]
            for handler in console_handlers:
                app_logger.removeHandler(handler)
        
        logger.info('MCP Server: ✓ Console handlers removed - only file logging active')
        
        # Run the server with explicit stdio transport
        import sys
        logger.info('MCP Server: Flushing stdout and stderr...')
        sys.stdout.flush()
        sys.stderr.flush()
        logger.info('MCP Server: ✓ Streams flushed')
        
        logger.info('MCP Server: About to call mcp.run(transport="stdio")...')
        logger.info('MCP Server: THIS IS THE LAST LOG BEFORE mcp.run() - if server times out, the problem is IN mcp.run()')
        logger.info('MCP Server: Running with show_banner=False and log_level=ERROR')
        
        # Suppress ALL FastMCP console logging by setting log level to ERROR
        # This prevents FastMCP's own logging from interfering with stdio JSON-RPC protocol
        logger.info('MCP Server: Setting FastMCP log level to ERROR to suppress console output')
        
        # Run without banner and with minimal logging to avoid interfering with stdio protocol
        mcp.run(transport="stdio", show_banner=False, log_level="ERROR")
        
        # This line should never be reached in normal operation
        logger.info('MCP Server: mcp.run() returned (unexpected - should run indefinitely)')
