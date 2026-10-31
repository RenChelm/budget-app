package org.ren.budgetapp;

import android.app.Activity;
import android.graphics.Insets;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.view.ActionMode;
import android.view.KeyEvent;
import android.view.KeyboardShortcutGroup;
import android.view.Menu;
import android.view.MenuItem;
import android.view.MotionEvent;
import android.view.SearchEvent;
import android.view.View;
import android.view.ViewConfiguration;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowManager;
import android.view.accessibility.AccessibilityEvent;

import java.util.ArrayList;
import java.util.List;

// KEEPS ANDROID'S BACK SWIPE FROM ALSO TAPPING WHAT IT STARTS ON //
// Android sends the start of an edge swipe to the app, then cancels it once it sees a back swipe.
// SDL passes that cancel on to Kivy as a normal finger lift, so the swipe also tapped whatever it
// started on (opening a week in History, closing a popup, ...). Touches that start in the back swipe
// zones are held until it's clear whether Android takes them; the ones it takes never reach Kivy.
//
// It sits in front of the activity's window callback, which sees every touch before any view does.
// That's plain Android, so it works with any SDL version and isn't undone when the app resumes.

public class BackSwipeFilter implements Window.Callback {
    private final Window.Callback app;
    private final Window window;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ArrayList<MotionEvent> held = new ArrayList<>();
    private final Runnable releaseHeld = this::release;
    private final int touchSlop;
    private final long holdTimeout;
    private boolean holding;
    private float downX, downY;

    private BackSwipeFilter(Activity activity, Window window, Window.Callback app) {
        this.app = app;
        this.window = window;
        touchSlop = ViewConfiguration.get(activity).getScaledTouchSlop();
        // Android stops treating a touch as a possible back swipe once it's held this long //
        holdTimeout = ViewConfiguration.getLongPressTimeout();
    }

    // Safe to call more than once; the window only ever gets one filter //
    public static void install(final Activity activity) {
        activity.runOnUiThread(() -> {
            Window window = activity.getWindow();
            Window.Callback current = window.getCallback();
            if (current != null && !(current instanceof BackSwipeFilter)) {
                window.setCallback(new BackSwipeFilter(activity, window, current));
            }
        });
    }

    // Holds a touch that starts in a back swipe zone until it's clear whether Android takes it //
    @Override
    public boolean dispatchTouchEvent(MotionEvent ev) {
        int action = ev.getActionMasked();

        if (action == MotionEvent.ACTION_DOWN) {
            discardHeld();
            if (!inBackSwipeZone(ev)) {
                return app.dispatchTouchEvent(ev);
            }
            holding = true;
            downX = ev.getX();
            downY = ev.getY();
            hold(ev);
            handler.postDelayed(releaseHeld, holdTimeout);
            return true;
        }

        if (!holding) {
            return app.dispatchTouchEvent(ev);
        }

        if (action == MotionEvent.ACTION_CANCEL) {
            // Android took it as a back swipe //
            discardHeld();
            return true;
        }

        if (action == MotionEvent.ACTION_MOVE) {
            float dx = Math.abs(ev.getX() - downX);
            float dy = Math.abs(ev.getY() - downY);

            // A mostly vertical drag is a scroll; a long sideways one Android would already have taken //
            boolean decided = (dy > dx && dy > touchSlop) || dx > touchSlop * 4;
            if (!decided) {
                hold(ev);
                return true;
            }
        }

        // Lifted (a tap), dragged away or a second finger came down: either way it isn't a back swipe //
        release();
        return app.dispatchTouchEvent(ev);
    }

    private boolean inBackSwipeZone(MotionEvent ev) {
        // Back swipes need Android 10+ with gesture navigation; with buttons the zones are 0 wide //
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q || ev.getToolType(0) != MotionEvent.TOOL_TYPE_FINGER) {
            return false;
        }

        View decor = window.getDecorView();
        WindowInsets insets = decor.getRootWindowInsets();
        if (insets == null) {
            return false;
        }

        Insets zones = Build.VERSION.SDK_INT >= Build.VERSION_CODES.R
            ? insets.getInsets(WindowInsets.Type.systemGestures())
            : insets.getSystemGestureInsets();

        float x = ev.getX();
        return x < zones.left || x > decor.getWidth() - zones.right;
    }

    private void hold(MotionEvent ev) {
        // Android reuses its events, so keep copies //
        held.add(MotionEvent.obtain(ev));
    }

    private void release() {
        // Hands the app everything held so far, in order //
        handler.removeCallbacks(releaseHeld);
        holding = false;
        for (MotionEvent ev : held) {
            app.dispatchTouchEvent(ev);
            ev.recycle();
        }
        held.clear();
    }

    private void discardHeld() {
        handler.removeCallbacks(releaseHeld);
        holding = false;
        for (MotionEvent ev : held) {
            ev.recycle();
        }
        held.clear();
    }

    // EVERYTHING ELSE GOES STRAIGHT TO THE ACTIVITY //

    @Override public boolean dispatchKeyEvent(KeyEvent event) { return app.dispatchKeyEvent(event); }
    @Override public boolean dispatchKeyShortcutEvent(KeyEvent event) { return app.dispatchKeyShortcutEvent(event); }
    @Override public boolean dispatchTrackballEvent(MotionEvent event) { return app.dispatchTrackballEvent(event); }
    @Override public boolean dispatchGenericMotionEvent(MotionEvent event) { return app.dispatchGenericMotionEvent(event); }
    @Override public boolean dispatchPopulateAccessibilityEvent(AccessibilityEvent event) { return app.dispatchPopulateAccessibilityEvent(event); }
    @Override public View onCreatePanelView(int featureId) { return app.onCreatePanelView(featureId); }
    @Override public boolean onCreatePanelMenu(int featureId, Menu menu) { return app.onCreatePanelMenu(featureId, menu); }
    @Override public boolean onPreparePanel(int featureId, View view, Menu menu) { return app.onPreparePanel(featureId, view, menu); }
    @Override public boolean onMenuOpened(int featureId, Menu menu) { return app.onMenuOpened(featureId, menu); }
    @Override public boolean onMenuItemSelected(int featureId, MenuItem item) { return app.onMenuItemSelected(featureId, item); }
    @Override public void onWindowAttributesChanged(WindowManager.LayoutParams attrs) { app.onWindowAttributesChanged(attrs); }
    @Override public void onContentChanged() { app.onContentChanged(); }
    @Override public void onWindowFocusChanged(boolean hasFocus) { app.onWindowFocusChanged(hasFocus); }
    @Override public void onAttachedToWindow() { app.onAttachedToWindow(); }
    @Override public void onDetachedFromWindow() { app.onDetachedFromWindow(); }
    @Override public void onPanelClosed(int featureId, Menu menu) { app.onPanelClosed(featureId, menu); }
    @Override public boolean onSearchRequested() { return app.onSearchRequested(); }
    @Override public boolean onSearchRequested(SearchEvent searchEvent) { return app.onSearchRequested(searchEvent); }
    @Override public ActionMode onWindowStartingActionMode(ActionMode.Callback callback) { return app.onWindowStartingActionMode(callback); }
    @Override public ActionMode onWindowStartingActionMode(ActionMode.Callback callback, int type) { return app.onWindowStartingActionMode(callback, type); }
    @Override public void onActionModeStarted(ActionMode mode) { app.onActionModeStarted(mode); }
    @Override public void onActionModeFinished(ActionMode mode) { app.onActionModeFinished(mode); }
    @Override public void onProvideKeyboardShortcuts(List<KeyboardShortcutGroup> data, Menu menu, int deviceId) { app.onProvideKeyboardShortcuts(data, menu, deviceId); }
    @Override public void onPointerCaptureChanged(boolean hasCapture) { app.onPointerCaptureChanged(hasCapture); }
}
