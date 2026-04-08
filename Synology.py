# -*- coding: utf-8 -*-
import sys
import os
import glob
import re
import subprocess

# When running as a py2app bundle, point Tcl/Tk at the script directories
# bundled into ``Contents/Resources/lib/``. Must happen before tkinter (or
# PIL.ImageTk, which imports tkinter) is loaded. Auto-detect the version
# because arm64 PBS Python ships Tk 8.6 and x86_64 PBS Python ships Tk 9.0,
# so the directory names differ between architectures.
if getattr(sys, "frozen", None) == "macosx_app":
    _resources = os.path.normpath(
        os.path.join(os.path.dirname(sys.executable), "..", "Resources")
    )

    def _highest_versioned_dir(prefix):
        candidates = []
        for path in glob.glob(os.path.join(_resources, "lib", prefix + "[0-9]*.[0-9]*")):
            m = re.fullmatch(re.escape(prefix) + r"(\d+)\.(\d+)", os.path.basename(path))
            if m and os.path.isdir(path):
                candidates.append(((int(m.group(1)), int(m.group(2))), path))
        candidates.sort()
        return candidates[-1][1] if candidates else None

    _tcl = _highest_versioned_dir("tcl")
    _tk = _highest_versioned_dir("tk")
    if _tcl:
        os.environ.setdefault("TCL_LIBRARY", _tcl)
    if _tk:
        os.environ.setdefault("TK_LIBRARY", _tk)

import logging
import logging.handlers
import webbrowser
import datetime
from PIL import Image, ImageTk
from syndecrypt import __main__
import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog
from tkinter import ttk


root = tk.Tk()
root.title("Cloud Sync Decryption Tool")
root.configure()
root.resizable(0,0)
root.withdraw()

# Tk on macOS unconditionally creates a *slave* Tcl interpreter for its
# built-in console subsystem during ``TkpInit``. Normally Tk's bundled
# ``console.tcl`` script hides the slave's default root window — but we
# stub that script to a no-op (it crashes on macOS 26 because Tk's menubar
# code passes a nil title to ``[NSMenuItem initWithTitle:]``), so the
# slave interpreter's empty root window stays visible as ``tk #2``.
# Use Tk's ``send`` IPC to withdraw it from our interpreter.
try:
    _our_appname = root.tk.call('tk', 'appname')
    _peers = root.tk.call('winfo', 'interps')
    for _peer in (_peers if isinstance(_peers, tuple) else _peers.split()):
        if _peer == _our_appname:
            continue
        try:
            root.tk.call('send', _peer, 'wm', 'withdraw', '.')
        except tk.TclError:
            pass
except tk.TclError:
    pass

# Resources packaged alongside this script. In a py2app .app the cwd is
# ``/`` when launched from Finder, so any relative resource path breaks.
_RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))

home_dir = os.path.expanduser('~')
log_file = os.path.join(home_dir, "synologycloudsyncdecrypttool.log")

logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
elogger=logging.getLogger('synology_logger')


def _bring_app_to_front():
    """macOS-only: nudge LaunchServices to make this process frontmost.
    Apps launched from Finder sometimes open behind whatever was already
    focused, requiring a Dock click to surface them. Uses ``open -b`` which
    routes through LaunchServices and needs no automation permissions —
    unlike ``tell application "System Events"``."""
    if sys.platform != "darwin":
        return
    try:
        subprocess.run(
            ["/usr/bin/open", "-b", "com.anojht.osx.synologycloudsyncdecryptiontool"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        logging.exception("failed to bring app to front")


top = tk.Toplevel()
top.config(width=100)
top.resizable(0,0)
top.attributes('-topmost', True)
top.title("DISCLAIMER")
top.configure()
msg = tk.Message(top, text="This software is provided for free. If you have paid for or have been asked to pay for this software, it is likely not legitimate. Please discontinue using this software and seek help from proper authorities.")
msg.pack(padx=10, pady=5)

def start():
    top.destroy()
    root.deiconify()
    root.attributes('-topmost', True)
    root.attributes('-topmost', False)

button = ttk.Button(top, text="OK", command=start)
button.pack(pady=5)
top.protocol('WM_DELETE_WINDOW', start)

# Force the disclaimer to the front and bring our process to the
# foreground — Finder-launched .app processes don't always get focus.
top.lift()
top.focus_force()
top.after(100, _bring_app_to_front)

method = tk.IntVar()
item = tk.IntVar()

methodlabel = ttk.Label(root,
                       text = "Select Decryption method",
                       justify = tk.LEFT,
                       padding = (20,0,0,0))

p = ttk.Radiobutton(root,
                   text = "Password",
                   variable = method,
                   value = 1)

pk = ttk.Radiobutton(root,
                    text = "Private Key",
                    variable = method,
                    value = 2)

password = ttk.Entry(root, show="*")

pkfilebox = ttk.Entry(root, state='disabled')
method.set(1)

def load_file():
    fname = tkinter.filedialog.askopenfilename()

    if fname:
        try:
            pkfilebox.config(state='normal')
            pkfilebox.delete(0, 'end')
            pkfilebox.insert(0, fname)
            pkfilebox.config(state='readonly')
        except:
            tkinter.messagebox.showwarning("Open Key File", "Failed to read file\n'%s'" % fname)
        return


pkbtn = ttk.Button(root, text="Select", command=load_file)

pulabel = ttk.Label(root,
                       text = "Public Key",
                       justify = tk.LEFT,
                       padding = (50,0,0,0))
pufilebox = ttk.Entry(root, state='disabled')

def load_filepu():
    fname = tkinter.filedialog.askopenfilename()

    if fname:
        try:
            pufilebox.config(state='normal')
            pufilebox.delete(0, 'end')
            pufilebox.insert(0, fname)
            pufilebox.config(state='readonly')
        except:
            tkinter.messagebox.showwarning("Open Key File", "Failed to read file\n'%s'" % fname)
        return


pubtn = ttk.Button(root, text="Select", command=load_filepu)

itemlabel = ttk.Label(root,
                     text = "Choose a file or folder to decrypt",
                     justify = tk.LEFT,
                     padding = (20,0,0,0))

file = ttk.Radiobutton(root,
                      text = "File",
                      variable = item,
                      value = 1)

folder = ttk.Radiobutton(root,
                        text = "Folder",
                        variable = item,
                        value = 2)

filebox = ttk.Entry(root, state='disabled', width=34)
item.set(1)

def load_decrypt_file():
    if (item.get() == 1):
        fname = tkinter.filedialog.askopenfilename()
    else:
        fname = tkinter.filedialog.askdirectory()

    if fname:
        try:
            filebox.config(state='normal')
            filebox.delete(0, 'end')
            filebox.insert(0, fname)
            filebox.config(state='readonly')
        except:
            tkinter.messagebox.showwarning("Open Key File", "Failed to read:\n'%s'" % fname)
        return

filebtn = ttk.Button(root, text="Select", command=load_decrypt_file)

outputlabel = ttk.Label(root,
                     text = "Choose output folder",
                     justify = tk.LEFT,
                     padding = (20,0,0,0))

outputbox = ttk.Entry(root, state='disabled', width=34)

def load_output():
    fname = tkinter.filedialog.askdirectory()

    if fname:
        try:
            outputbox.config(state='normal')
            outputbox.delete(0, 'end')
            outputbox.insert(0, fname)
            outputbox.config(state='readonly')
        except:
            tkinter.messagebox.showwarning("Open Key File", "Failed to read:\n'%s'" % fname)
        return


outputbtn = ttk.Button(root, text="Select", command=load_output)

w = tk.ttk.Separator(root)

def validate():
    if method.get() == 1:
        if password.get() != "":
            if filebox.get() != "":
                if outputbox.get() != "":
                    if os.path.dirname(filebox.get()) == outputbox.get():
                        tkinter.messagebox.showwarning("Decryption", "Output folder cannot be the same folder as the encrypted file/folder!")
                        return
                    elif outputbox.get().startswith(os.path.abspath(filebox.get())+os.sep):
                        tkinter.messagebox.showwarning("Decryption", "Output folder cannot be inside the encryption folder!")
                        return
                    elif os.path.basename(filebox.get()) == os.path.basename(outputbox.get()):
                        if os.path.dirname(filebox.get()) == os.path.dirname(outputbox.get()):
                            tkinter.messagebox.showwarning("Decryption", "Output folder cannot be the same folder as the encrypted folder!")
                            return
                    try:
                        run_tool()
                    except Exception as e:
                        elogger.error(e, exc_info=e)
                        tkinter.messagebox.showwarning("Decryption", "Failed to decrypt file(s), please raise an issue using the support button located in the about option of the application menu")
                    else:
                        tkinter.messagebox.showinfo("Decryption", "Files have successfully been decrypted and can be found in the destination folder")
                else:
                    tkinter.messagebox.showwarning("Decryption", "Please choose output folder!")
            else:
                tkinter.messagebox.showwarning("Decryption", "Please choose file or folder to decrypt!")
        else:
            tkinter.messagebox.showwarning("Decryption", "Please enter your password!")
    elif method.get() == 2:
        if pkfilebox.get() != "":
            if pufilebox.get() != "":
                if filebox.get() != "":
                    if outputbox.get() != "":
                        if os.path.dirname(filebox.get()) == outputbox.get():
                            tkinter.messagebox.showwarning("Decryption", "Output folder cannot be the same folder as the encrypted file/folder!")
                            return
                        elif outputbox.get().startswith(os.path.abspath(filebox.get())+os.sep):
                            tkinter.messagebox.showwarning("Decryption", "Output folder cannot be inside the encryption folder!")
                            return
                        elif os.path.basename(filebox.get()) == os.path.basename(outputbox.get()):
                            if os.path.dirname(filebox.get()) == os.path.dirname(outputbox.get()):
                                tkinter.messagebox.showwarning("Decryption", "Output folder cannot be the same folder as the encrypted folder!")
                                return
                        try:
                            run_tool()
                        except Exception as e:
                            elogger.error(e, exc_info=e)
                            tkinter.messagebox.showwarning("Decryption", "Failed to decrypt file(s), please raise an issue using the support button located in the about option of the application menu")
                        else:
                            tkinter.messagebox.showinfo("Decryption", "Files have successfully been decrypted and can be found in the destination folder")
                    else:
                        tkinter.messagebox.showwarning("Decryption", "Please choose output folder!")
                else:
                    tkinter.messagebox.showwarning("Decryption", "Please choose file or folder to decrypt!")
            else:
                tkinter.messagebox.showwarning("Decryption", "Please select your public key file!")
        else:
            tkinter.messagebox.showwarning("Decryption", "Please select your private key file!")


def reset_app():
    method.set(1)
    password.delete(0, 'end')
    pkfilebox.config(state='normal')
    pkfilebox.delete(0, 'end')
    pkfilebox.config(state='disabled')
    pufilebox.config(state='normal')
    pufilebox.delete(0, 'end')
    pufilebox.config(state='disabled')
    item.set(1)
    filebox.config(state='normal')
    filebox.delete(0, 'end')
    filebox.config(state='disabled')
    outputbox.config(state='normal')
    outputbox.delete(0, 'end')
    outputbox.config(state='disabled')


reset = ttk.Button(root, text="Reset", command=reset_app)

decrypt = ttk.Button(root, text="Decrypt", command=validate)


methodlabel.grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=(10,2))

p.grid(row=1, column=1, sticky=tk.W, padx=30)
pk.grid(row=2, column=1, sticky=tk.W, padx=30)

password.grid(row=1, column=2)
pkfilebox.grid(row=2, column=2)
pkbtn.grid(row=2, column=3)

pulabel.grid(row=3, column=1, sticky=tk.W)
pufilebox.grid(row=3, column=2)
pubtn.grid(row=3, column=3)

itemlabel.grid(row=4, column=1, columnspan=2, sticky=tk.W, pady=(10,2))

file.grid(row=5, column=1, sticky=tk.W, padx=30)
folder.grid(row=5, column=2, sticky=tk.W, padx=30)

filebox.grid(row=6, column=1, columnspan=2, sticky=tk.E)
filebtn.grid(row=6, column=3)

outputlabel.grid(row=7, column=1, columnspan=2, sticky=tk.W, pady=(10,2))

outputbox.grid(row=8, column=1, columnspan=2, sticky=tk.E)
outputbtn.grid(row=8, column=3)

w.grid(row=9, columnspan=4, sticky=tk.E + tk.W, pady=(8, 5))

reset.grid(row=10, column=2, sticky=tk.E, padx=(0,4), pady=(0,5))
decrypt.grid(row=10, column=3, padx=(0,5), pady=(0,5))

def run_tool():
    if method.get() == 1:
        pword = password.get()
        out = outputbox.get()
        input = filebox.get()
        __main__.main(['-p', pword, out, input])
    elif method.get() == 2:
        pkey = pkfilebox.get()
        pukey = pufilebox.get()
        out = outputbox.get()
        input = filebox.get()
        __main__.main(['-k', pkey, pukey, out, input])


def open_url(url):
    webbrowser.open_new(url)


def about_dialog():
    win = tk.Toplevel()
    win.title("About")
    win.configure()
    win.resizable(0,0)

    img = ImageTk.PhotoImage(Image.open(os.path.join(_RESOURCE_DIR, "app.gif")).resize((128, 128), Image.Resampling.LANCZOS))
    icon = ttk.Label(win, image=img)
    icon.image = img
    name = ttk.Label(win, text="Open Source Synology Cloud Sync Decryption Tool", font=("San Francisco", 14, "bold"))
    copytext = "© " + str(datetime.datetime.now().year) + " - Created by Anojh Thayaparan"
    author = ttk.Label(win, text=copytext)
    license = tk.Text(win, height=8, width=31, font=("San Francisco", 12), wrap='word')
    license.insert("1.0", "\nLICENSE:\n This app is provided as is to the user, without any liabilities, warranties or guarantees from the author. Any damages arising from use or misuse of the software is not a liability of the author.\nFor more information refer to the COPYRIGHTS file shipped with the application.")
    license.tag_config("center", justify='center')
    license.tag_add("center", "1.0", "end")
    license.config(state='disabled', highlightbackground='grey', highlightcolor='grey', borderwidth=1, highlightthickness=1)
    support = ttk.Button(win, text="Support", command=lambda: open_url("https://github.com/anojht/synology-cloud-sync-decrypt-tool/issues"))
    donate = ttk.Button(win, text="Donate", command=lambda: open_url("https://www.paypal.me/Anojh"))

    icon.grid(row=0, column=1, padx=10)
    name.grid(row=1, column=1, padx=10)
    author.grid(row=2, column=1)
    license.grid(row=3, column=1, pady=10)
    donate.grid(row=4, column=1, padx=(0,80), pady=(0,5))
    support.grid(row=4, column=1, padx=(90,0), pady=(0,5))


root.createcommand('tkAboutDialog', about_dialog)

root.mainloop()
