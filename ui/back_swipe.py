from kivy.utils import platform

## KEEPS ANDROID'S BACK SWIPE FROM ALSO TAPPING WHAT IT STARTS ON ##

def filter_back_swipes():
    # Android's back swipe starts as a normal touch, and Kivy took it as a tap on whatever it started on #
    # (opening a week in History, closing a popup, ...); android_src/.../BackSwipeFilter.java holds those touches back #
    if platform != "android":
        return

    from jnius import autoclass
    from android import mActivity
    autoclass("org.ren.budgetapp.BackSwipeFilter").install(mActivity)
