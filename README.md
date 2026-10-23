# Screencast Keys (Blender 4.2+ / 5.x)

Shows the keys you press and your mouse clicks in Blender's 3D View, so people
watching a screen recording or tutorial can follow along.

---

## 🚀 Quick start (new to Blender or GitHub? Start here!)

You don't need a GitHub account, and you don't need to unzip anything.

### Step 1: Download the add-on

1. On this GitHub page, look at the **right-hand side** for a section called
   **Releases**, and click the newest release (the one marked **Latest**).
   *(On a phone or narrow window, Releases is further down the page.)*
2. Under **Assets**, click the file that starts with
   **`screencast_keys_classic-`** and ends in **`.zip`** to download it.
3. **Don't unzip it.** Blender wants the zip file just as it is. It will be in
   your **Downloads** folder.

> ⚠️ Don't use the green **Code → Download ZIP** button. That's the source code,
> not the add-on, and Blender won't install it.

### Step 2: Install it in Blender

1. Open Blender (version 4.2 or newer).
2. In the top menu, click **Edit → Preferences…**
3. In the Preferences window, click **Get Extensions** on the left.
4. At the top right, click the small **⌄** (down-arrow) button and choose
   **Install from Disk…**
5. Find the zip in your **Downloads** folder, click it, then click
   **Install from Disk**.
6. Click **Add-ons** on the left and check that **Screencast Keys** has a tick
   next to it. If it doesn't, click the box to tick it.
7. Close the Preferences window. Blender saves the setting automatically. (If
   it doesn't, click the **☰** menu at the bottom left of Preferences and choose
   **Save Preferences**.)

You only need to do steps 1 and 2 once.

### Step 3: Turn it on

1. Move your mouse over the big 3D area in the middle of Blender (the
   **3D Viewport**).
2. Press **N** on the keyboard. A panel opens on the right side of the viewport.
3. Along the edge of that panel are some tabs. Click the one called
   **Screencast Keys**.
4. Click **Start Display**. Now every key you press and every mouse click shows
   up in the bottom-left corner of the 3D view. 🎉
5. To turn it off, click **Stop Display**.

**Shortcut:** with your mouse over the 3D view, press **Shift + Alt + C** to
turn it on or off.

### Step 4: Make it look how you want (optional)

While it's running, the same panel lets you change the text size, where it sits
on screen, its color, how long keys stay visible, whether a mouse picture is
shown, and more. Just try the settings. You can't break anything.

**Putting it somewhere else on screen:**

- **Position X** moves it from the left edge (0) to the right edge (100).
  **Position Y** moves it from the bottom (0) to the top (100).
- The **Left / Center / Right** buttons under Position choose how the keys line
  up:
  - **Left:** keys line up on the left and get longer to the right. Good for
    the left side of the screen.
  - **Center:** keys are centered on the position. Good for the middle.
  - **Right:** keys line up on the right and get longer to the left. Good for
    the right side of the screen, for example X at 90 to 100.
- **Icon Side: Left / Right** chooses which side of the keys the little mouse
  picture goes on.

It always stays inside the 3D view, even when the N panel is open.

Press **N** again to hide the panel. The key display keeps working.

### Getting a newer version later

Download the newest zip from **Releases** and install it the same way
(Step 2). It replaces the old version, and your settings stay the same.

---

## About

This is an updated version of the classic Screencast Keys add-on by Paulo Gomes,
Bart Crouch, John E. Herrenyo, Gaia Clary and Pablo Vazquez. Its drawing code has
been rewritten for Blender's modern `gpu` module (the old OpenGL `bgl` calls no
longer exist), so it runs on Blender 4.2 and later, including 5.2.

## Quick reference (for experienced users)

- **Install:** download the zip from Releases, then **Edit → Preferences → Get
  Extensions → ⌄ → Install from Disk…**
- **Use:** in the 3D View, press **N** to open the sidebar and go to the
  **Screencast Keys** tab.
- Click **Start Display** (or press **Shift+Alt+C** with the mouse over the 3D View).
- Once it's running, the panel lets you change text size, position,
  alignment (left / center / right), mouse icon side, colors,
  fade time, the mouse icon, the background box, the "last operator" label and
  an elapsed-time counter.
- Click **Stop Display** (or press Shift+Alt+C again) to turn it off.

## Build the zip yourself

From this folder:

```
blender --command extension build
```

## License

GPL-2.0-or-later. See [LICENSE](LICENSE).
