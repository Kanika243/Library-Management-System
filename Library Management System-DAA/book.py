import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from pymongo import MongoClient
import heapq
import qrcode
from PIL import Image, ImageTk
from bson import ObjectId

# Database Setup
client = MongoClient("mongodb://localhost:27017/")
db = client["library_db"]
books_collection = db["books"]

# Function to Build Dynamic Graph from Books Collection
def build_library_graph():
    graph = {"Entrance": {}, "Exit": {}}
    books = books_collection.find({}, {"title": 1})  
    previous_title = "Entrance"
    
    for book in books:
        title = book["title"]
        graph[title] = {}
        graph[previous_title][title] = 1  # Assigning a weight of 1 to simulate distance
        graph[title]["Exit"] = 1
        previous_title = title
    
    return graph

class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System")
        self.root.geometry("700x500")
        self.root.configure(bg="#ADD8E6")  # Light blue background
        self.library_graph = build_library_graph()
        self.setup_ui()

    def setup_ui(self):
        ttk.Label(self.root, text="Library Management System", font=("Times New Roman", 16)).pack(pady=10)
        
        self.tree = ttk.Treeview(self.root, columns=("ID", "Title", "Author", "Genre", "Year", "Availability"), show="headings")
        for col in ("ID", "Title", "Author", "Genre", "Year", "Availability"):
            self.tree.heading(col, text=col)
        self.tree.pack(pady=20)
        
        ttk.Button(self.root, text="Add Book", command=self.add_book).pack(pady=5)
        ttk.Button(self.root, text="Borrow Book", command=self.borrow_book).pack(pady=5)
        ttk.Button(self.root, text="Return Book", command=self.return_book).pack(pady=5)
        ttk.Button(self.root, text="Find Shortest Path to Book", command=self.find_shortest_path).pack(pady=5)
        ttk.Button(self.root, text="Search Book", command=self.search_book).pack(pady=5)
        ttk.Button(self.root, text="Generate QR Code", command=self.generate_qr_code).pack(pady=5)
        
        self.load_books()

    def add_book(self):
        def save_book():
            title = entry_title.get()
            author = entry_author.get()
            genre = entry_genre.get()
            year = entry_year.get()
            book = {"title": title, "author": author, "genre": genre, "year": int(year), "availability": "Available"}
            books_collection.insert_one(book)
            self.load_books()
            add_win.destroy()
        
        add_win = tk.Toplevel(self.root)
        add_win.title("Add Book")
        tk.Label(add_win, text="Title").pack()
        entry_title = tk.Entry(add_win)
        entry_title.pack()
        tk.Label(add_win, text="Author").pack()
        entry_author = tk.Entry(add_win)
        entry_author.pack()
        tk.Label(add_win, text="Genre").pack()
        entry_genre = tk.Entry(add_win)
        entry_genre.pack()
        tk.Label(add_win, text="Year").pack()
        entry_year = tk.Entry(add_win)
        entry_year.pack()
        tk.Button(add_win, text="Save", command=save_book).pack()

    def load_books(self):
        self.tree.delete(*self.tree.get_children())
        for book in books_collection.find():
            self.tree.insert("", "end", values=(str(book["_id"]), book["title"], book["author"], book["genre"], book["year"], book["availability"]))
        
        self.library_graph = build_library_graph()  # Refresh graph dynamically

    def borrow_book(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a book to borrow.")
            return
        book_id = self.tree.item(selected_item, "values")[0]
        books_collection.update_one({"_id": ObjectId(book_id)}, {"$set": {"availability": "Borrowed"}})
        self.load_books()
        messagebox.showinfo("Success", "Book borrowed successfully!")

    def return_book(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a book to return.")
            return
        book_id = self.tree.item(selected_item, "values")[0]
        books_collection.update_one({"_id": ObjectId(book_id)}, {"$set": {"availability": "Available"}})
        self.load_books()
        messagebox.showinfo("Success", "Book returned successfully!")

    def dijkstra(self, graph, start, end):
        heap = [(0, start, [])]  # (distance, node, path)
        distances = {node: float('inf') for node in graph}
        distances[start] = 0

        while heap:
            curr_distance, curr_node, path = heapq.heappop(heap)
            if curr_node == end:
                return path + [end], curr_distance
            
            for neighbor, weight in graph[curr_node].items():
                distance = curr_distance + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    heapq.heappush(heap, (distance, neighbor, path + [curr_node]))
        return None, float('inf')

    def find_shortest_path(self):
        book_title = simpledialog.askstring("Find Path", "Enter Book Title:")
        if not book_title:
            return

        if book_title not in self.library_graph:
            messagebox.showerror("Error", "Book location not found!")
            return

        path, steps = self.dijkstra(self.library_graph, "Entrance", book_title)
        if steps == float('inf'):
            messagebox.showwarning("Warning", "No path found!")
        else:
            messagebox.showinfo("Shortest Path", f"Path: {' -> '.join(path)}\nSteps: {steps}")

    def search_book(self):
        title = simpledialog.askstring("Search Book", "Enter Book Title:")
        book = books_collection.find_one({"title": title})
        if book:
            messagebox.showinfo("Search Result", f"Title: {book['title']}\nAuthor: {book['author']}\nGenre: {book['genre']}\nYear: {book['year']}\nAvailability: {book['availability']}")
        else:
            messagebox.showwarning("Not Found", "No book found with that title.")

    def generate_qr_code(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a book to generate QR code.")
            return
        book_details = self.tree.item(selected_item, "values")
        qr = qrcode.make(f"Title: {book_details[1]}\nAuthor: {book_details[2]}")
        qr.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()
