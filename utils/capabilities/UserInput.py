
class UserInput:
    """Allows getting an input from the user"""
    
    @staticmethod
    def get_terminal_input(prompt: str) -> str:
        """
        This tool displays a prompt in the terminal and returns the user's input.
        
        Args:
        prompt (str): The prompt to display to the user.

        Returns:
        str: The user's input from the terminal.
        """
        user_input = input(prompt + " ")
        return user_input