from .ai_agent_enhanced import AIAgentEnhanced
import argparse
import sys
import os
import json
from ..core.database_utils import DatabaseManager
from ..core.documentation_analyzer import DocumentationAnalyzer
import uuid
import click
import logging
from typing import Dict, Any
import networkx as nx
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
import numpy as np

# Set up logging and console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class AIAgentCLI:
    def __init__(self):
        self.agent = AIAgentEnhanced()
        self.session_id = str(uuid.uuid4())
        self.db_manager = DatabaseManager()
        self.current_repo = None
        
        # Verify database setup
        self.db_manager.verify_database_state()
        self.load_state()

    def load_state(self):
        """Load active repositories for this session"""
        try:
            # First try to get session-specific repos
            repos = self.db_manager.get_active_repositories(self.session_id)
            
            # If no session-specific repos, get all repos
            if not repos:
                repos = self.db_manager.get_active_repositories()
            
            if repos:
                print("\nAvailable repositories:")
                for repo in repos:
                    print(f"- {repo['name']} (Last analyzed: {repo.get('last_analyzed', 'Never')})")
                # Set current_repo to first available repo
                self.current_repo = repos[0]['name']
            else:
                print("\nNo repositories available. Use 'analyze <repo_url>' to add one.")
            
        except Exception as e:
            logger.error(f"Error loading session state: {e}")

    def use_repository(self, repo_name: str):
        """Add a repository to this session"""
        try:
            self.db_manager.set_current_repository(
                repo_name, 
                f"./temp/{repo_name}", 
                self.session_id
            )
            print(f"Added {repo_name} to current session")
        except Exception as e:
            print(f"Error adding repository: {str(e)}")

    def save_state(self):
        """Save the current repository state to both database and state file"""
        try:
            # Save to database
            if self.current_repo:
                self.db_manager.set_current_repository(self.current_repo)

            # Save to state file as backup
            state = {
                'current_repo': self.current_repo
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Error saving state: {str(e)}")

    def show_current_repo(self):
        """Show current repository status"""
        if not self.current_repo:
            print("\nNo repository currently loaded.")
            return
        
        try:
            repo_info = self.db_manager.get_repository_info(self.current_repo)
            if repo_info:
                print(f"\nCurrent repository: {self.current_repo}")
                print(f"Last analyzed: {repo_info.get('last_analyzed', 'Never')}")
                
                # Get update status
                update_info = self.agent.check_repository_updates(self.current_repo)
                if update_info.get('needs_update'):
                    print(f"Status: Needs update ({update_info.get('reason')})")
                else:
                    print("Status: Up to date")
            else:
                print("\nNo repository currently loaded.")
                
        except Exception as e:
            logger.error(f"Error showing repository status: {e}")

    def start_cli(self):
        print("\n=== AI Agent Enhanced CLI ===")
        print("Type 'help' for commands or 'exit' to quit")
        self.show_current_repo()  # Show current repo status at startup
        
        while True:
            try:
                command = input("\nWhat would you like to do? > ").strip()
                
                if command.lower() == 'exit':
                    print("Goodbye!")
                    break
                elif command.lower() == 'help':
                    self.show_help()
                elif command.lower() == 'current':  # New command
                    self.show_current_repo()
                elif command.lower().startswith('analyze '):
                    repo_url = command[8:].strip()
                    self.analyze_repo(repo_url)
                elif command.lower().startswith('ask '):
                    question = command[4:].strip()
                    self.ask_question(question)
                elif command.lower() == 'status':
                    self.verify_analysis()
                elif command.lower().startswith('use '):
                    repo_name = command[4:].strip()
                    if repo_name == 'llama_index':
                        self.current_repo = "llama_index"
                        self.save_state()
                        print(f"Now using {repo_name}")
                        self.show_current_repo()
                    else:
                        print(f"Repository {repo_name} not found in analyzed repositories")
                elif command.lower() == 'list':
                    self.list_repositories()
                else:
                    print("Unknown command. Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")

    def show_help(self):
        print("""
Available commands:
- analyze <repo_url>  : Analyze a new repository
- ask <question>      : Ask a question about the current repository
- current            : Show current repository status
- status             : Show current analysis status
- list               : List all repositories in database
- use <repo_name>    : Switch to a previously analyzed repository
- help               : Show this help message
- exit               : Exit the program
        """)

    def analyze_repo(self, repo_url: str):
        """Analyze a new repository"""
        try:
            print(f"\nAnalyzing repository: {repo_url}")
            # Call analyze_repo instead of analyze_repository
            result = self.agent.analyze_repo(repo_url)
            if result:
                print("Analysis complete!")
                return True
            else:
                print("Analysis failed.")
                return False
        except Exception as e:
            logger.error(f"Error analyzing repository: {str(e)}")
            return False

    def _display_analysis_summary(self, understanding: Dict[str, Any]):
        """Display summary of codebase analysis"""
        # Create summary table
        table = Table(title="Codebase Analysis Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        if understanding.get('structure'):
            table.add_row(
                "Modules",
                str(len(understanding['structure'].get('modules', [])))
            )
            table.add_row(
                "Dependencies",
                str(len(understanding['structure'].get('dependencies', [])))
            )
        
        if understanding.get('graph_analysis'):
            table.add_row(
                "Core Components",
                str(len(understanding['graph_analysis'].get('core_components', [])))
            )
            table.add_row(
                "Code Patterns",
                str(len(understanding['graph_analysis'].get('patterns', [])))
            )
        
        console.print(table)

    @click.command()
    @click.option('--type', type=click.Choice(['dependency', 'community', 'knowledge']),
                 help='Type of visualization to generate')
    def visualize(self, type: str):
        """Generate and display codebase visualizations"""
        if not self.current_repo:
            console.print("[red]No repository currently analyzed[/red]")
            return

        viz_type_map = {
            'dependency': 'dependency_graph',
            'community': 'community_clusters',
            'knowledge': 'knowledge_flow'
        }

        viz_data = self.agent.generate_visualizations(viz_type_map[type])
        if viz_data:
            self._display_visualization(type, viz_data)

    def _display_visualization(self, viz_type: str, data: Dict):
        """Display visualization using matplotlib"""
        plt.figure(figsize=(12, 8))
        
        if viz_type == 'dependency':
            G = nx.DiGraph()
            for node in data['nodes']:
                G.add_node(node['name'], **node)
            for edge in data['edges']:
                G.add_edge(edge['source'], edge['target'])
                
            pos = nx.spring_layout(G)
            nx.draw(G, pos, with_labels=True, node_color='lightblue',
                   node_size=1000, arrowsize=20)
            
        elif viz_type == 'community':
            # Create community subplot
            communities = data
            colors = plt.cm.get_cmap('tab20')(np.linspace(0, 1, len(communities)))
            
            for idx, (community, color) in enumerate(zip(communities, colors)):
                plt.scatter(idx, len(community['nodes']), 
                          color=color, s=100, label=f"Community {idx}")
                
            plt.xlabel('Community ID')
            plt.ylabel('Number of Nodes')
            
        elif viz_type == 'knowledge':
            G = nx.DiGraph()
            for node in data['nodes']:
                G.add_node(node['name'], **node)
            for flow in data['flows']:
                G.add_edge(flow['source'], flow['target'], 
                          weight=flow['weight'])
                
            pos = nx.kamada_kawai_layout(G)
            edges = nx.draw_networkx_edges(G, pos, edge_color='gray',
                                         width=[G[u][v]['weight'] for u,v in G.edges()])
            nodes = nx.draw_networkx_nodes(G, pos, node_color='lightgreen',
                                         node_size=1000)
            labels = nx.draw_networkx_labels(G, pos)

        plt.title(f"{viz_type.title()} Visualization")
        plt.tight_layout()
        plt.show()

    @click.command()
    @click.argument('component_name')
    def analyze_component(self, component_name: str):
        """Analyze a specific component"""
        if not self.current_repo:
            console.print("[red]No repository currently analyzed[/red]")
            return

        impact = self.agent.query_codebase('component_impact', {'name': component_name})
        if impact:
            table = Table(title=f"Component Analysis: {component_name}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in impact.items():
                table.add_row(key, str(value))
            
            console.print(table)

    def ask_question(self, question):
        if not self.current_repo:
            print("No repository loaded. Previously analyzed: llama_index")
            print("To continue with llama_index, type 'use llama_index'")
            return

        try:
            print(f"\nAnalyzing question: {question}")
            
            # Get repository context
            repo_path = "./local_repo_path"  # or store this from process_new_repository
            
            # Get documentation first (especially README.md for "what is" questions)
            doc_analysis = None
            if os.path.exists(os.path.join(repo_path, "README.md")):
                with open(os.path.join(repo_path, "README.md"), 'r', encoding='utf-8') as f:
                    doc_analyzer = DocumentationAnalyzer()
                    doc_analysis = doc_analyzer.analyze(f.read())

            # Get other context
            context = {
                'documentation': doc_analysis,
                'project_structure': self.agent.analyze_project_structure(repo_path),
                'framework_patterns': self.agent.analyze_framework_patterns("python"),
                'dependencies': self.agent.build_dependency_graph()
            }
            
            # Here you would format the context and question for your AI model
            print("\nBased on the repository analysis:")
            if doc_analysis and doc_analysis.get('examples'):
                print("Found relevant documentation and examples")
            if context['project_structure']:
                print("Found relevant project structure information")
            
            # Add your AI model response generation here
            if doc_analysis:
                print("\nRepository Overview:")
                overview = doc_analysis.get('usage', [''])[0]
                print(overview)
                
        except Exception as e:
            print(f"Error processing question: {str(e)}")
            import traceback
            print(traceback.format_exc())

    def verify_analysis(self):
        """Add this method to AIAgentCLI to check database status"""
        if self.current_repo:
            print("\nDatabase Status:")
            
            # Check PostgreSQL
            try:
                # Get count of stored snippets
                snippet_count = self.agent.get_stored_snippets_count()
                print(f"- Code Snippets in PostgreSQL: {snippet_count}")
            except Exception as e:
                print(f"PostgreSQL Error: {str(e)}")
            
            # Check Neo4j
            try:
                # Get count of relationships
                relationship_count = self.agent.get_stored_relationships_count()
                print(f"- Code Relationships in Neo4j: {relationship_count}")
            except Exception as e:
                print(f"Neo4j Error: {str(e)}")

    def list_repositories(self):
        """List all available repositories"""
        try:
            repos = self.db_manager.get_active_repositories()  # No session_id for all repos
            if repos:
                print("\nAvailable repositories:")
                for repo in repos:
                    status = "[Current]" if repo['name'] == self.current_repo else ""
                    print(f"- {repo['name']} (Last analyzed: {repo.get('last_analyzed', 'Never')}) {status}")
            else:
                print("\nNo repositories found.")
        except Exception as e:
            logger.error(f"Error listing repositories: {e}")

    def show_repository_status(self, repo_name: str = None):
        """Show detailed status of repository analysis"""
        if repo_name is None and self.current_repo:
            repo_name = self.current_repo

        if not repo_name:
            print("No repository specified")
            return

        try:
            print(f"\nRepository Status for {repo_name}:")
            
            # Get repository metadata
            repo_info = self.db_manager.get_repository_info(repo_name)
            if repo_info:
                print(f"Last analyzed: {repo_info['last_analyzed']}")
                print(f"Status: {repo_info['status']}")
                
                # Get embedding statistics
                print("\nEmbeddings:")
                print(f"- Code snippets: {self.agent.get_stored_snippets_count(repo_name)}")
                print(f"- Documentation: {self.agent.get_stored_doc_count(repo_name)}")
                
                # Get graph statistics
                print("\nCode Graph:")
                print(f"- Nodes: {self.agent.get_node_count(repo_name)}")
                print(f"- Relationships: {self.agent.get_stored_relationships_count(repo_name)}")
                
                # Get language statistics
                print("\nLanguages:")
                for lang, count in self.agent.get_language_statistics(repo_name).items():
                    print(f"- {lang}: {count} files")
                    
            else:
                print("Repository not found in database")
                
        except Exception as e:
            print(f"Error getting repository status: {str(e)}")

    def get_repository_count(self):
        """Get count of repositories in database"""
        try:
            repos = self.db_manager.get_active_repositories()
            return len(repos)
        except Exception as e:
            print(f"Error getting repository count: {str(e)}")
            return 0

def main():
    cli = AIAgentCLI()
    cli.start_cli()

if __name__ == "__main__":
    main()
