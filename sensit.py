#!/usr/bin/env python3
"""
SenSIt - Sensitive Information Scanner & Validator
Main CLI entry point
"""
import asyncio
import click
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.scanner import SecretsScanner
from core.config import Config
from core.logger import logger, setup_logger
from output.cli_reporter import CLIReporter
from output.json_exporter import JSONExporter


@click.command()
@click.option('--url', '-u', help='Target URL to scan')
@click.option('--file', '-f', 'file_path', help='Single file to scan')
@click.option('--directory', '-d', 'dir_path', help='Directory to scan recursively')
@click.option('--output', '-o', help='Output file path (JSON)')
@click.option('--config', '-c', help='Custom config file path')
@click.option('--no-ai', is_flag=True, help='Disable AI validation')
@click.option('--no-api', is_flag=True, help='Disable live API validation')
@click.option('--ai-provider', type=click.Choice(['openai', 'gemini', 'ollama'], case_sensitive=False), help='AI provider (openai/gemini/ollama)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Minimal output')
@click.option('--json-only', is_flag=True, help='Output JSON only (no CLI)')
def main(url, file_path, dir_path, output, config, no_ai, no_api, ai_provider, verbose, quiet, json_only):
    """
    SenSIt - Sensitive Information Scanner & Validator
    
    Identifies and validates hardcoded secrets using:
    - Regex pattern matching (50+ patterns)
    - Shannon entropy analysis
    - AI-powered contextual validation (OpenAI)
    - Live API validation
    
    Examples:
        sensit.py --url https://example.com
        sensit.py --directory /path/to/code --output report.json
        sensit.py --file config.js --no-api
    """
    
    # Setup logging
    if quiet:
        setup_logger(level=40)  # ERROR only
    elif verbose:
        setup_logger(level=10)  # DEBUG
    else:
        setup_logger(level=20)  # INFO
    
    # Load configuration
    cfg = Config(config)
    
    # Override config with CLI flags
    if no_ai:
        cfg.set('validation.enable_ai_validation', False)
    if no_api:
        cfg.set('validation.enable_api_validation', False)
    if ai_provider:
        cfg.set('ai_provider', ai_provider.lower())
    
    # Initialize scanner
    scanner = SecretsScanner(cfg)
    
    # Initialize reporters
    cli_reporter = CLIReporter(verbose=verbose)
    json_exporter = JSONExporter()
    
    # Print banner
    if not quiet and not json_only:
        cli_reporter.print_banner()
    
    # Validate input
    if not any([url, file_path, dir_path]):
        click.echo("Error: Must specify --url, --file, or --directory", err=True)
        click.echo("Run 'sensit.py --help' for usage information", err=True)
        sys.exit(1)
    
    # Run scan
    try:
        if url:
            finding = asyncio.run(scanner.scan_url(url))
        elif file_path:
            finding = asyncio.run(scanner.scan_file(file_path))
        elif dir_path:
            finding = asyncio.run(scanner.scan_directory(dir_path))
        
        # Output results
        if json_only:
            # JSON output only
            print(json_exporter.export_string(finding))
        else:
            # CLI output
            if not quiet:
                cli_reporter.print_finding(finding)
                
                if finding.secrets and verbose:
                    cli_reporter.print_summary_table(finding)
        
        # Export to file if specified
        if output:
            output_file = json_exporter.export(finding, output)
            if not quiet:
                logger.info(f"Report exported to: {output_file}")
        
        # Exit code based on findings
        if finding.get_confirmed_secrets():
            sys.exit(2)  # Confirmed secrets found
        elif finding.secrets:
            sys.exit(1)  # Potential secrets found
        else:
            sys.exit(0)  # No secrets found
            
    except KeyboardInterrupt:
        logger.warning("\nScan interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
