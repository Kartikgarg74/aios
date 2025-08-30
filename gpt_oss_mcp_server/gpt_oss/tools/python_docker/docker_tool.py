import asyncio
import os
import tempfile
from typing import AsyncGenerator, List, Optional, Dict, Any

# Define simple message classes to avoid dependency on openai_harmony
class TextContent:
    def __init__(self, text: str):
        self.text = text

class Author:
    def __init__(self, role: str, name: str):
        self.role = role
        self.name = name

class Role:
    TOOL = "tool"

class Message:
    def __init__(self, author: Author, content: List[TextContent]):
        self.author = author
        self.content = content

class PythonTool:
    """Tool for executing Python code in a Docker container."""

    def __init__(self):
        """Initialize the Python Docker tool."""
        pass

    async def process(self, message: Message) -> AsyncGenerator[Message, None]:
        """Process a message containing Python code.
        
        Args:
            message: A message containing Python code to execute.
            
        Returns:
            An async generator yielding messages with execution results.
        """
        code = message.content[0].text if message.content else ""
        
        if not code.strip():
            yield Message(
                author=Author(role=Role.TOOL, name="python"),
                content=[TextContent(text="No code provided.")]
            )
            return

        # Create a temporary file for the Python code
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        try:
            # Execute the Python code
            process = await asyncio.create_subprocess_exec(
                "python", temp_file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Prepare the output message
            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""
            
            result = output if not error else f"Error:\n{error}"
            
            yield Message(
                author=Author(role=Role.TOOL, name="python"),
                content=[TextContent(text=result)]
            )
            
        except Exception as e:
            yield Message(
                author=Author(role=Role.TOOL, name="python"),
                content=[TextContent(text=f"Execution error: {str(e)}")]
            )
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)