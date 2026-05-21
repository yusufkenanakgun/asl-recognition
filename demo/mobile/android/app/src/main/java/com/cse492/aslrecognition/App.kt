package com.cse492.aslrecognition

import android.app.Application
import com.cse492.aslrecognition.di.AppContainer

class App : Application() {

    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
    }
}
