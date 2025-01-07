import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, date
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from logger import ErrorLogger
import traceback

class DatabaseUI:
    """
    A graphical user interface for managing database operations.
    
    This class provides a GUI for various database operations including adding customers,
    passes, classes, purchases, and attendance records. It interfaces with a Supabase
    backend for data storage.
    """

    def __init__(self, root):
        """
        Initialize the DatabaseUI application.

        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.root.title("Database Management System")
        self.root.geometry("600x400")
        
        # Initialize Supabase connection using environment variables
        load_dotenv()
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_SECRET_KEY")
        self.supabase: Client = create_client(url, key)

        # Initialize error logger
        self.error_logger = ErrorLogger()
        
        # Create main frame with padding
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.create_widgets()

        # Create progress bar (hidden by default)
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.grid(row=6, column=0, pady=20, sticky='ew')
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            mode='determinate',
            length=300
        )
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack()
        self.progress_bar.pack()
        self.progress_frame.grid_remove()  # Hide initially

    def create_widgets(self):
        """Create and arrange all GUI widgets in the main window."""
        # Title
        title = ttk.Label(self.main_frame, text="Database Management System", 
                         font=('Helvetica', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=2, pady=20)

        # Create buttons for each database operation
        ttk.Button(self.main_frame, text="Add Customer Data", 
                  command=self.add_customers_dialog).grid(row=1, column=0, pady=5, padx=10, sticky='ew')
        ttk.Button(self.main_frame, text="Add Pass", 
                  command=self.add_pass_dialog).grid(row=2, column=0, pady=5, padx=10, sticky='ew')
        ttk.Button(self.main_frame, text="Add Classes", 
                  command=self.add_classes_dialog).grid(row=3, column=0, pady=5, padx=10, sticky='ew')
        ttk.Button(self.main_frame, text="Add Purchases", 
                  command=self.add_purchases_dialog).grid(row=4, column=0, pady=5, padx=10, sticky='ew')
        ttk.Button(self.main_frame, text="Add Attendances", 
                  command=self.add_attendances_dialog).grid(row=5, column=0, pady=5, padx=10, sticky='ew')

    def select_file(self):
        """
        Open a file dialog for selecting CSV files.

        Returns:
            str: The selected file path or empty string if cancelled
        """
        filename = filedialog.askopenfilename(
            title="Select a CSV file",
            filetypes=[("CSV files", "*.csv")]
        )
        return filename

    def add_customers_dialog(self):
        """
        Create a dialog for adding customer data.
        
        Prompts for last pull date and CSV file selection.
        Validates date format and processes the customer data.
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Customer Data")
        dialog.geometry("400x200")

        ttk.Label(dialog, text="Last Pull Date (YYYY-MM-DD):").pack(pady=5)
        date_entry = ttk.Entry(dialog)
        date_entry.pack(pady=5)

        def select_and_process():
            """Process the customer data with selected file and entered date."""
            try:
                last_pull = datetime.strptime(date_entry.get(), '%Y-%m-%d').date()
                file_path = self.select_file()
                if file_path:
                    from main import add_to_customers
                    
                    self.show_progress(True)
                    self.progress_label['text'] = "Processing customer data..."
                    self.root.update()
                    
                    count = add_to_customers(self.supabase, file_path, last_pull)
                    messagebox.showinfo("Success", f"{count} customer(s) added successfully!")
                    dialog.destroy()
            except ValueError as e:
                self.handle_error("Add Customers", e, {"file": file_path, "last_pull": date_entry.get()})
            except Exception as e:
                self.handle_error("Add Customers", e, {
                    "file": file_path,
                    "last_pull": date_entry.get(),
                    "traceback": traceback.format_exc()
                })
            finally:
                self.show_progress(False)

        ttk.Button(dialog, text="Select File and Process", 
                  command=select_and_process).pack(pady=20)

    def add_pass_dialog(self):
        """Handle adding pass data from a CSV file to the database."""
        file_path = self.select_file()
        if file_path:
            try:
                from main import add_pass
                
                self.show_progress(True)
                self.progress_label['text'] = "Processing pass data..."
                self.root.update()
                
                count, duplicates = add_pass(self.supabase, file_path)
                
                # Create success message
                message = f"{count} pass(es) added successfully!"
                if duplicates:
                    message += f"\n\nThe following passes were skipped (already exist):\n{', '.join(duplicates)}"
                
                messagebox.showinfo("Success", message)
                
            except ValueError as e:
                self.handle_error("Add Passes", e, {"file": file_path})
            except Exception as e:
                self.handle_error("Add Passes", e, {
                    "file": file_path,
                    "traceback": traceback.format_exc()
                })
            finally:
                self.show_progress(False)

    def add_classes_dialog(self):
        """Handle adding class data from a CSV file to the database."""
        file_path = self.select_file()
        if file_path:
            try:
                from main import add_class
                
                self.show_progress(True)
                self.progress_label['text'] = "Processing class data..."
                self.root.update()
                
                count = add_class(self.supabase, file_path)
                messagebox.showinfo("Success", f"{count} class(es) added successfully!")
            except ValueError as e:
                self.handle_error("Add Classes", e, {"file": file_path})
            except Exception as e:
                self.handle_error("Add Classes", e, {
                    "file": file_path,
                    "traceback": traceback.format_exc()
                })
            finally:
                self.show_progress(False)

    def add_purchases_dialog(self):
        """Handle adding purchase data from a CSV file to the database."""
        file_path = self.select_file()
        if file_path:
            try:
                from main import add_purchases
                
                self.show_progress(True)
                self.progress_label['text'] = "Processing purchase data..."
                self.root.update()
                
                count = add_purchases(self.supabase, file_path)
                messagebox.showinfo("Success", f"{count} purchase(s) added successfully!")
            except ValueError as e:
                self.handle_error("Add Purchases", e, {"file": file_path})
            except Exception as e:
                self.handle_error("Add Purchases", e, {
                    "file": file_path,
                    "traceback": traceback.format_exc()
                })
            finally:
                self.show_progress(False)

    def show_progress(self, show=True):
        """Show or hide the progress bar."""
        if show:
            self.progress_frame.grid()
        else:
            self.progress_frame.grid_remove()
        self.root.update()

    def update_progress(self, current, total, operation):
        """Update the progress bar and label."""
        percentage = (current / total) * 100
        self.progress_bar['value'] = percentage
        self.progress_label['text'] = f"{operation}: {percentage:.1f}%"
        self.root.update()

    def handle_error(self, operation, error, details=None):
        """Log the error and show error message to user."""
        self.error_logger.log_error(operation, error, details)
        error_msg = f"An error occurred during {operation}.\nCheck logs for details.\n\nError: {str(error)}"
        messagebox.showerror("Error", error_msg)

    def add_attendances_dialog(self):
        """Handle adding attendance data from a CSV file to the database."""
        file_path = self.select_file()
        if file_path:
            try:
                from main import add_attendances
                
                # Show progress bar
                self.show_progress(True)
                self.progress_label['text'] = "Processing attendance data..."
                self.root.update()
                
                count = add_attendances(self.supabase, file_path, self.update_progress)
                messagebox.showinfo("Success", f"{count} attendance record(s) added successfully!")
                
            except ValueError as e:
                self.handle_error("Add Attendances", e, {"file": file_path})
            except Exception as e:
                self.handle_error("Add Attendances", e, {
                    "file": file_path,
                    "traceback": traceback.format_exc()
                })
            finally:
                self.show_progress(False)

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseUI(root)
    root.mainloop() 