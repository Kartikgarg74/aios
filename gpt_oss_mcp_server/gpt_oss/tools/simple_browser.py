# This file is intentionally left empty to avoid circular imports.
# The SimpleBrowserTool and ExaBackend classes are now defined directly in browser_server.py

@dataclass
class Message:
    content: List[Any]

@dataclass
class TextContent:
    text: str

class SimpleBrowserTool:
    def __init__(self, backend: ExaBackend):
        self.backend = backend
        
    async def search(self, query: str, topn: int = 10, source: Optional[str] = None) -> AsyncIterator[Message]:
        """Search for information related to a query"""
        # Initialize the browser if needed
        self.backend.initialize_driver()
        
        # Perform a search using a search engine
        self.backend.driver.get(f"https://www.google.com/search?q={query}")
        
        # Extract search results
        try:
            search_results = WebDriverWait(self.backend.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.g"))
            )
            
            results = []
            for i, result in enumerate(search_results[:topn]):
                try:
                    title = result.find_element(By.CSS_SELECTOR, "h3").text
                    link = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    snippet = result.find_element(By.CSS_SELECTOR, "div.VwiC3b").text
                    results.append(f"[{i+1}] {title}\n{link}\n{snippet}\n")
                except Exception:
                    continue
            
            # Store the current page in history
            self.backend.current_page = "search_results"
            self.backend.history.append({
                "type": "search",
                "query": query,
                "results": results
            })
            
            # Return search results
            yield Message(content=[TextContent(text="\n".join(results))])
            
        except Exception as e:
            yield Message(content=[TextContent(text=f"Error performing search: {str(e)}")])
    
    async def open(self, id: Union[int, str] = -1, cursor: int = -1, 
                  loc: int = -1, num_lines: int = -1, 
                  view_source: bool = False, source: Optional[str] = None) -> AsyncIterator[Message]:
        """Open a link or navigate to a page location"""
        self.backend.initialize_driver()
        
        try:
            # If id is a string, treat it as a URL
            if isinstance(id, str):
                self.backend.driver.get(id)
                page_source = self.backend.driver.page_source
                title = self.backend.driver.title
                url = self.backend.driver.current_url
                
                # Store the current page
                self.backend.current_page = {
                    "url": url,
                    "title": title,
                    "source": page_source if view_source else None
                }
                
                # Extract visible text
                text_content = self.backend.driver.find_element(By.TAG_NAME, "body").text
                lines = text_content.split("\n")
                
                # Determine which lines to show
                start_line = loc if loc > 0 else 0
                end_line = start_line + num_lines if num_lines > 0 else len(lines)
                
                # Format the output
                output = f"[{cursor if cursor > 0 else len(self.backend.history)}] {title} - {url}\n"
                output += "\n".join([f"L{i+1}: {line}" for i, line in enumerate(lines[start_line:end_line])])
                
                yield Message(content=[TextContent(text=output)])
            
            # If id is an integer, try to open from history
            elif isinstance(id, int) and id >= 0 and id < len(self.backend.history):
                history_item = self.backend.history[id]
                if history_item["type"] == "search" and "results" in history_item:
                    yield Message(content=[TextContent(text="\n".join(history_item["results"]))])
                else:
                    yield Message(content=[TextContent(text=f"Cannot display history item of type {history_item['type']}")])
            
            else:
                yield Message(content=[TextContent(text="Invalid ID or cursor")])
                
        except Exception as e:
            yield Message(content=[TextContent(text=f"Error opening link: {str(e)}")])
    
    async def find(self, pattern: str, cursor: int = -1) -> AsyncIterator[Message]:
        """Find exact matches of a pattern in the current page"""
        if not self.backend.current_page:
            yield Message(content=[TextContent(text="No page is currently open")])
            return
        
        try:
            # Get the page source
            page_source = self.backend.driver.page_source
            
            # Use JavaScript to find all occurrences
            script = f"""
            var body = document.body.innerText;
            var pattern = {pattern};
            var matches = [];
            var lines = body.split('\n');
            
            for (var i = 0; i < lines.length; i++) {{  
                if (lines[i].includes(pattern)) {{  
                    matches.push({{line: i+1, text: lines[i]}});
                }}
            }}
            
            return matches;
            """
            
            matches = self.backend.driver.execute_script(script)
            
            if not matches:
                yield Message(content=[TextContent(text=f"No matches found for '{pattern}'")])
            else:
                result = f"Found {len(matches)} matches for '{pattern}':\n"
                for match in matches:
                    result += f"L{match['line']}: {match['text']}\n"
                
                yield Message(content=[TextContent(text=result)])
                
        except Exception as e:
            yield Message(content=[TextContent(text=f"Error finding pattern: {str(e)}")])