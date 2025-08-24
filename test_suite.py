#!/usr/bin/env python3
"""
Comprehensive Testing Suite for AI Operating System MCP Servers
Validates all server integrations and functionality.
"""

import asyncio
import json
import time
import requests
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIOSTestSuite:
    """Comprehensive test suite for AI OS MCP servers"""
    
    def __init__(self):
        self.base_urls = {
            'main': 'http://localhost:9000',
            'browser': 'http://localhost:8001',
            'system': 'http://localhost:8002',
            'communication': 'http://localhost:8003',
            'ide': 'http://localhost:8004',
            'github': 'http://localhost:8005',
            'voice_ui': 'http://localhost:8006'
        }
        self.test_results = {}
        
    async def run_health_checks(self) -> Dict[str, bool]:
        """Run health checks for all servers"""
        results = {}
        
        for server_name, base_url in self.base_urls.items():
            try:
                response = requests.get(f"{base_url}/health", timeout=5)
                results[server_name] = response.status_code == 200
                logger.info(f"✓ {server_name} health check: {'PASS' if results[server_name] else 'FAIL'}")
            except Exception as e:
                results[server_name] = False
                logger.error(f"✗ {server_name} health check failed: {e}")
                
        return results
    
    async def test_browser_server(self) -> Dict[str, Any]:
        """Test browser automation server"""
        results = {'passed': 0, 'failed': 0, 'tests': []}
        
        try:
            # Test browser launch
            response = requests.post(f"{self.base_urls['browser']}/tools/launch_browser", 
                                   json={'url': 'https://example.com'}, timeout=10)
            results['tests'].append({
                'name': 'browser_launch',
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response': response.json() if response.status_code == 200 else response.text
            })
            
            # Test screenshot
            response = requests.post(f"{self.base_urls['browser']}/tools/take_screenshot", 
                                   json={'url': 'https://example.com'}, timeout=10)
            results['tests'].append({
                'name': 'take_screenshot',
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response': response.json() if response.status_code == 200 else response.text
            })
            
        except Exception as e:
            results['tests'].append({
                'name': 'browser_server_tests',
                'status': 'ERROR',
                'error': str(e)
            })
            
        return results
    
    async def test_system_server(self) -> Dict[str, Any]:
        """Test system operations server"""
        results = {'passed': 0, 'failed': 0, 'tests': []}
        
        try:
            # Test system info
            response = requests.get(f"{self.base_urls['system']}/tools/system_info", timeout=5)
            results['tests'].append({
                'name': 'system_info',
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response': response.json() if response.status_code == 200 else response.text
            })
            
            # Test file operations
            test_file = Path('/tmp/test_file.txt')
            response = requests.post(f"{self.base_urls['system']}/tools/create_file", 
                                   json={'path': str(test_file), 'content': 'test content'}, timeout=5)
            results['tests'].append({
                'name': 'create_file',
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response': response.json() if response.status_code == 200 else response.text
            })
            
            # Cleanup
            if test_file.exists():
                test_file.unlink()
                
        except Exception as e:
            results['tests'].append({
                'name': 'system_server_tests',
                'status': 'ERROR',
                'error': str(e)
            })
            
        return results
    
    async def test_communication_server(self) -> Dict[str, Any]:
        """Test communication server"""
        results = {'passed': 0, 'failed': 0, 'tests': []}
        
        try:
            # Test email validation
            response = requests.post(f"{self.base_urls['communication']}/tools/validate_email", 
                                   json={'email': 'test@example.com'}, timeout=5)
            results['tests'].append({
                'name': 'email_validation',
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response': response.json() if response.status_code == 200 else response.text
            })
            
            # Test contact management
            response = requests.get(f"{self.base_urls['communication']}/tools/get_contacts", timeout=5)
            results['tests'].append({
                'name': 'get_contacts',
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response': response.json() if response.status_code == 200 else response.text
            })
            
        except Exception as e:
            results['tests'].append({
                'name': 'communication_server_tests',
                'status': 'ERROR',
                'error': str(e)
            })
            
        return results
    
    async def test_ide_server(self) -> Dict[str, Any]:
        """Test IDE integration server"""
        results = {'passed': 0, 'failed': 0, 'tests': []}
        
        try:
            # Test VS Code detection
            response = requests.get(f"{self.base_urls['ide']}/tools/vscode_status", timeout=5)
            results['tests'].append({
                'name': 'vscode_status',
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response': response.json() if response.status_code == 200 else response.text
            })
            
            # Test git operations
            response = requests.post(f"{self.base_urls['ide']}/tools/git_status", 
                                   json={'repo_path': '/tmp'}, timeout=5)
            results['tests'].append({
                'name': 'git_status',
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response': response.json() if response.status_code == 200 else response.text
            })
            
        except Exception as e:
            results['tests'].append({
                'name': 'ide_server_tests',
                'status': 'ERROR',
                'error': str(e)
            })
            
        return results
    
    async def test_github_server(self) -> Dict[str, Any]:
        """Test GitHub Actions server"""
        results = {'passed': 0, 'failed': 0, 'tests': []}
        
        try:
            # Test repository operations
            response = requests.post(f"{self.base_urls['github']}/tools/validate_repo", 
                                   json={'repo_url': 'https://github.com/example/repo'}, timeout=5)
            results['tests'].append({
                'name': 'repo_validation',
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response': response.json() if response.status_code == 200 else response.text
            })
            
            # Test workflow operations
            response = requests.get(f"{self.base_urls['github']}/tools/get_workflows", 
                                  json={'repo': 'example/repo'}, timeout=5)
            results['tests'].append({
                'name': 'get_workflows',
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response': response.json() if response.status_code == 200 else response.text
            })
            
        except Exception as e:
            results['tests'].append({
                'name': 'github_server_tests',
                'status': 'ERROR',
                'error': str(e)
            })
            
        return results
    
    async def test_voice_ui_server(self) -> Dict[str, Any]:
        """Test voice/UI server"""
        results = {'passed': 0, 'failed': 0, 'tests': []}
        
        try:
            # Test TTS functionality
            response = requests.post(f"{self.base_urls['voice_ui']}/tools/text_to_speech", 
                                   json={'text': 'Hello, this is a test'}, timeout=5)
            results['tests'].append({
                'name': 'text_to_speech',
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response': response.json() if response.status_code == 200 else response.text
            })
            
            # Test screenshot capability
            response = requests.post(f"{self.base_urls['voice_ui']}/tools/take_screenshot", timeout=5)
            results['tests'].append({
                'name': 'take_screenshot',
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response': response.json() if response.status_code == 200 else response.text
            })
            
        except Exception as e:
            results['tests'].append({
                'name': 'voice_ui_tests',
                'status': 'ERROR',
                'error': str(e)
            })
            
        return results
    
    async def test_integration_flow(self) -> Dict[str, Any]:
        """Test complete integration flow"""
        results = {'passed': 0, 'failed': 0, 'tests': []}
        
        try:
            # Test query stacking
            query_data = {
                'steps': [
                    {
                        'server': 'system',
                        'tool': 'create_file',
                        'parameters': {'path': '/tmp/test_integration.txt', 'content': 'Integration test'}
                    },
                    {
                        'server': 'browser',
                        'tool': 'take_screenshot',
                        'parameters': {'url': 'https://example.com'}
                    }
                ]
            }
            
            response = requests.post(f"{self.base_urls['main']}/query/create", 
                                   json=query_data, timeout=10)
            results['tests'].append({
                'name': 'query_stacking_integration',
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response': response.json() if response.status_code == 200 else response.text
            })
            
        except Exception as e:
            results['tests'].append({
                'name': 'integration_flow',
                'status': 'ERROR',
                'error': str(e)
            })
            
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        logger.info("Starting AI OS Test Suite...")
        
        # Health checks first
        health_results = await self.run_health_checks()
        
        # Individual server tests
        browser_tests = await self.test_browser_server()
        system_tests = await self.test_system_server()
        communication_tests = await self.test_communication_server()
        ide_tests = await self.test_ide_server()
        github_tests = await self.test_github_server()
        voice_ui_tests = await self.test_voice_ui_server()
        integration_tests = await self.test_integration_flow()
        
        # Compile results
        final_results = {
            'health_checks': health_results,
            'browser_server': browser_tests,
            'system_server': system_tests,
            'communication_server': communication_tests,
            'ide_server': ide_tests,
            'github_server': github_tests,
            'voice_ui_server': voice_ui_tests,
            'integration_flow': integration_tests,
            'timestamp': time.time()
        }
        
        # Save results
        with open('test_results.json', 'w') as f:
            json.dump(final_results, f, indent=2)
        
        logger.info("Test suite completed. Results saved to test_results.json")
        return final_results

def run_test_server():
    """Run the test server for validation"""
    print("AI OS Test Server - Running comprehensive validation...")
    
    async def main():
        test_suite = AIOSTestSuite()
        results = await test_suite.run_all_tests()
        
        # Print summary
        print("\n=== TEST SUMMARY ===")
        for server, status in results['health_checks'].items():
            print(f"{server}: {'✓ ONLINE' if status else '✗ OFFLINE'}")
        
        print("\nDetailed results saved to test_results.json")
        
    asyncio.run(main())

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        run_test_server()
    else:
        asyncio.run(AIOSTestSuite().run_all_tests())