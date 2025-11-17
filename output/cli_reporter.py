"""CLI output reporter"""
from colorama import Fore, Style, init
from tabulate import tabulate
from models.secret import Finding, Secret

init(autoreset=True)


class CLIReporter:
    """Beautiful CLI output"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
    
    def print_banner(self):
        """Print SenSIt banner"""
        banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   {Fore.GREEN}███████{Fore.CYAN}╗{Fore.GREEN}███████{Fore.CYAN}╗{Fore.GREEN}███{Fore.CYAN}╗   {Fore.GREEN}██{Fore.CYAN}╗{Fore.GREEN}███████{Fore.CYAN}╗{Fore.GREEN}██{Fore.CYAN}╗{Fore.GREEN}████████{Fore.CYAN}╗          ║
║   {Fore.GREEN}██{Fore.CYAN}╔════╝{Fore.GREEN}██{Fore.CYAN}╔════╝{Fore.GREEN}████{Fore.CYAN}╗  {Fore.GREEN}██{Fore.CYAN}║{Fore.GREEN}██{Fore.CYAN}╔════╝{Fore.GREEN}██{Fore.CYAN}║╚══{Fore.GREEN}██{Fore.CYAN}╔══╝          ║
║   {Fore.GREEN}███████{Fore.CYAN}╗{Fore.GREEN}█████{Fore.CYAN}╗  {Fore.GREEN}██{Fore.CYAN}╔{Fore.GREEN}██{Fore.CYAN}╗ {Fore.GREEN}██{Fore.CYAN}║{Fore.GREEN}███████{Fore.CYAN}╗{Fore.GREEN}██{Fore.CYAN}║   {Fore.GREEN}██{Fore.CYAN}║             ║
║   ╚════{Fore.GREEN}██{Fore.CYAN}║{Fore.GREEN}██{Fore.CYAN}╔══╝  {Fore.GREEN}██{Fore.CYAN}║╚{Fore.GREEN}██{Fore.CYAN}╗{Fore.GREEN}██{Fore.CYAN}║╚════{Fore.GREEN}██{Fore.CYAN}║{Fore.GREEN}██{Fore.CYAN}║   {Fore.GREEN}██{Fore.CYAN}║             ║
║   {Fore.GREEN}███████{Fore.CYAN}║{Fore.GREEN}███████{Fore.CYAN}╗{Fore.GREEN}██{Fore.CYAN}║ ╚{Fore.GREEN}████{Fore.CYAN}║{Fore.GREEN}███████{Fore.CYAN}║{Fore.GREEN}██{Fore.CYAN}║   {Fore.GREEN}██{Fore.CYAN}║             ║
║   ╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝   ╚═╝             ║
║                                                               ║
║        {Fore.YELLOW}Sensitive Information Scanner & Validator{Fore.CYAN}           ║
║                    {Fore.WHITE}v1.0.0 - by viruz{Fore.CYAN}                       ║
╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(banner)
    
    def print_finding(self, finding: Finding):
        """Print scan results"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Scan Results for: {Fore.WHITE}{finding.target}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        # Summary
        print(f"{Fore.GREEN}[+]{Style.RESET_ALL} Files scanned: {finding.total_files_scanned}")
        print(f"{Fore.GREEN}[+]{Style.RESET_ALL} Total secrets found: {finding.total_secrets_found}")
        print(f"{Fore.GREEN}[+]{Style.RESET_ALL} Scan duration: {finding.scan_duration:.2f}s")
        
        # Count by severity
        critical = len([s for s in finding.secrets if s.severity == "CRITICAL"])
        high = len([s for s in finding.secrets if s.severity == "HIGH"])
        medium = len([s for s in finding.secrets if s.severity == "MEDIUM"])
        low = len([s for s in finding.secrets if s.severity == "LOW"])
        
        print(f"\n{Fore.CYAN}Severity Breakdown:{Style.RESET_ALL}")
        if critical > 0:
            print(f"  {Fore.RED}● CRITICAL: {critical}{Style.RESET_ALL}")
        if high > 0:
            print(f"  {Fore.YELLOW}● HIGH: {high}{Style.RESET_ALL}")
        if medium > 0:
            print(f"  {Fore.BLUE}● MEDIUM: {medium}{Style.RESET_ALL}")
        if low > 0:
            print(f"  {Fore.WHITE}● LOW: {low}{Style.RESET_ALL}")
        
        # Count by status
        confirmed = len([s for s in finding.secrets if s.status == "CONFIRMED"])
        likely = len([s for s in finding.secrets if s.status == "LIKELY"])
        
        print(f"\n{Fore.CYAN}Validation Status:{Style.RESET_ALL}")
        if confirmed > 0:
            print(f"  {Fore.RED}✓ CONFIRMED (Live API): {confirmed}{Style.RESET_ALL}")
        if likely > 0:
            print(f"  {Fore.YELLOW}~ LIKELY (High AI confidence): {likely}{Style.RESET_ALL}")
        
        # Print secrets
        if finding.secrets:
            print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Detected Secrets:{Style.RESET_ALL}\n")
            
            for i, secret in enumerate(finding.secrets, 1):
                self.print_secret(secret, i)
        else:
            print(f"\n{Fore.GREEN}✓ No secrets found!{Style.RESET_ALL}")
    
    def print_secret(self, secret: Secret, index: int = 1):
        """Print a single secret"""
        # Color based on severity
        severity_colors = {
            "CRITICAL": Fore.RED,
            "HIGH": Fore.YELLOW,
            "MEDIUM": Fore.BLUE,
            "LOW": Fore.WHITE
        }
        color = severity_colors.get(secret.severity, Fore.WHITE)
        
        # Status icon
        status_icons = {
            "CONFIRMED": f"{Fore.RED}✓ CONFIRMED",
            "LIKELY": f"{Fore.YELLOW}~ LIKELY",
            "POSSIBLE": f"{Fore.BLUE}? POSSIBLE",
            "UNVERIFIED": f"{Fore.WHITE}○ UNVERIFIED"
        }
        status = status_icons.get(secret.status, "○ UNKNOWN")
        
        print(f"{color}┌─ Secret #{index} ─ {secret.severity} ─────────────────────────────────{Style.RESET_ALL}")
        print(f"{color}│{Style.RESET_ALL}")
        print(f"{color}│{Style.RESET_ALL} Type: {Fore.WHITE}{secret.type}{Style.RESET_ALL}")
        print(f"{color}│{Style.RESET_ALL} Status: {status}{Style.RESET_ALL}")
        print(f"{color}│{Style.RESET_ALL} Location: {Fore.CYAN}{secret.location}:{secret.line_number}{Style.RESET_ALL}")
        
        # Truncate value for display
        display_value = secret.value[:60] + '...' if len(secret.value) > 60 else secret.value
        print(f"{color}│{Style.RESET_ALL} Value: {Fore.YELLOW}{display_value}{Style.RESET_ALL}")
        
        print(f"{color}│{Style.RESET_ALL}")
        print(f"{color}│{Style.RESET_ALL} Entropy: {secret.entropy:.2f}")
        print(f"{color}│{Style.RESET_ALL} AI Confidence: {secret.ai_confidence:.0f}%")
        
        if secret.ai_reasoning:
            print(f"{color}│{Style.RESET_ALL} AI Reasoning: {secret.ai_reasoning[:80]}")
        
        if secret.api_valid is not None:
            api_status = f"{Fore.GREEN}✓ Valid" if secret.api_valid else f"{Fore.RED}✗ Invalid"
            print(f"{color}│{Style.RESET_ALL} API Validation: {api_status}{Style.RESET_ALL}")
            
            if secret.api_details:
                print(f"{color}│{Style.RESET_ALL} API Details: {secret.api_details}")
        
        if self.verbose and secret.context:
            print(f"{color}│{Style.RESET_ALL}")
            print(f"{color}│{Style.RESET_ALL} Context:")
            context_lines = secret.context.split('\n')[:5]
            for line in context_lines:
                print(f"{color}│{Style.RESET_ALL}   {Fore.WHITE}{line[:70]}{Style.RESET_ALL}")
        
        print(f"{color}└{'─'*68}{Style.RESET_ALL}\n")
    
    def print_summary_table(self, finding: Finding):
        """Print summary table"""
        if not finding.secrets:
            return
        
        table_data = []
        for secret in finding.secrets:
            table_data.append([
                secret.type,
                secret.severity,
                secret.status,
                f"{secret.ai_confidence:.0f}%",
                "✓" if secret.api_valid else ("✗" if secret.api_valid is False else "-"),
                secret.location[:40] + '...' if len(secret.location) > 40 else secret.location
            ])
        
        headers = ["Type", "Severity", "Status", "AI Conf", "API", "Location"]
        print(f"\n{Fore.CYAN}Summary Table:{Style.RESET_ALL}\n")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
