# SlideStag Connection Client

Copyright (C) 2022 by Michael Ikemann

For more information visit http://www.scistag.org

A client for iOS to remotely connect to a SlideStag application hosted on a server, your
development pc or an embedded device and interact with it like a local UI application. 

# Note

This is a very early proof of concept to evaluate the performance of a remote hosted UI and 
accessing it using iOS and Android devices. Feel free to play around with it, but it's
my first Dart & Flutter application so be aware of surprised and pragmatic code. ;-)

# Getting started

* Basic Flutter knowledge required. There are many awesome "Hello world" tutorials out there.
  If you were able to start your first Flutter app on your iPad you may continue here :).
* Create a  basic SlideStag application and run it via SlideStag4Flask. Host it on an ip other than
127.0.0.1, e.g. 0.0.0.0. Use tools such as 'ifconfig' or your network settings to find our
your IP. For most home routers it begins with something like 192.168.
* Copy the file assets/config_template.json to assets/config.json in the same directory.
* Exchange the IP in config.json with your IP... and if you also wrote a professional app and
registered it as SlideApplication with it's own name... also exchange the name SlideStag
accordingly.
* Adjust the signing settings in the iOS runner's project configuration.
* Build and run this app
* Have fun!