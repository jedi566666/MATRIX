"""Standalone offline desktop workspace; the private Pro interface is excluded."""
def run(data_dir=None):
    import tkinter as tk
    from tkinter import ttk, messagebox
    from .team_store import Store
    store=Store(data_dir)
    root=tk.Tk();root.title('MATRIX — local mission workspace');root.geometry('960x620')
    root.minsize(680,480)
    frame=ttk.Frame(root,padding=20);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='MATRIX',font=('Segoe UI',26,'bold')).pack(anchor='w')
    ttk.Label(frame,text='Offline coordination · no model calls · no cloud credentials').pack(anchor='w',pady=(0,16))
    fields={}
    for name in ('project','agent','objective','deliverables'):
        row=ttk.Frame(frame);row.pack(fill='x',pady=3)
        ttk.Label(row,text=name.title(),width=14).pack(side='left')
        fields[name]=ttk.Entry(row);fields[name].pack(side='left',fill='x',expand=True)
    table=ttk.Treeview(frame,columns=('project','agent','state'),show='headings')
    for name in ('project','agent','state'):table.heading(name,text=name.title())
    def refresh():
        for item in table.get_children():table.delete(item)
        for item in store.list():table.insert('', 'end',iid=item['id'],values=(item['project'],item['agent'],item['state']))
    def create():
        try:store.create(**{name:entry.get() for name,entry in fields.items()});refresh()
        except (ValueError,OSError) as error:messagebox.showerror('Cannot create mission',str(error))
    controls=ttk.Frame(frame);controls.pack(fill='x',pady=12)
    ttk.Button(controls,text='Create mission',command=create).pack(side='left')
    ttk.Button(controls,text='Refresh',command=refresh).pack(side='left',padx=8)
    table.pack(fill='both',expand=True);refresh();root.mainloop()
