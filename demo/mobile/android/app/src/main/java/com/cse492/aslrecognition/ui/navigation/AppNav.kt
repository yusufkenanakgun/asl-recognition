package com.cse492.aslrecognition.ui.navigation

import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.systemBars
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Abc
import androidx.compose.material.icons.filled.ChatBubble
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.outlined.Abc
import androidx.compose.material.icons.outlined.ChatBubbleOutline
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.cse492.aslrecognition.R
import com.cse492.aslrecognition.ui.home.HomeScreen
import com.cse492.aslrecognition.ui.letters.LettersScreen
import com.cse492.aslrecognition.ui.theme.AppColors
import com.cse492.aslrecognition.ui.words.WordsScreen

private data class Tab(
    val route: String,
    val labelRes: Int,
    val iconOutlined: ImageVector,
    val iconFilled: ImageVector,
)

private val Tabs = listOf(
    Tab(Routes.Home, R.string.tab_home, Icons.Outlined.Home, Icons.Filled.Home),
    Tab(Routes.Letters, R.string.tab_letters, Icons.Outlined.Abc, Icons.Filled.Abc),
    Tab(Routes.Words, R.string.tab_words, Icons.Outlined.ChatBubbleOutline, Icons.Filled.ChatBubble),
)

@Composable
fun AppNav() {
    val nav = rememberNavController()
    val backStack by nav.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination?.route ?: Routes.Home

    Scaffold(
        // Status bar inset'i içerikten almıyoruz — kamera tepeye kadar uzansın.
        // Home gibi ekranlar kendi statusBarsPadding()'ini ekler.
        contentWindowInsets = WindowInsets.systemBars.only(WindowInsetsSides.Bottom),
        bottomBar = {
            NavigationBar(
                containerColor = AppColors.Background,
                tonalElevation = 0.dp,
            ) {
                Tabs.forEach { tab ->
                    val selected = backStack?.destination?.hierarchy?.any { it.route == tab.route } == true
                    NavigationBarItem(
                        selected = selected,
                        onClick = {
                            if (currentRoute == tab.route) return@NavigationBarItem
                            nav.navigate(tab.route) {
                                popUpTo(nav.graph.startDestinationId) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = {
                            Icon(
                                imageVector = if (selected) tab.iconFilled else tab.iconOutlined,
                                contentDescription = null,
                            )
                        },
                        label = { Text(stringResource(tab.labelRes)) },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = AppColors.TealDark,
                            selectedTextColor = AppColors.TextPrimary,
                            indicatorColor = AppColors.TealContainer,
                            unselectedIconColor = AppColors.TextSecondary,
                            unselectedTextColor = AppColors.TextSecondary,
                        ),
                    )
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = nav,
            startDestination = Routes.Home,
            modifier = Modifier.padding(padding),
        ) {
            composable(Routes.Home) {
                HomeScreen(
                    onOpenLetters = {
                        nav.navigate(Routes.Letters) {
                            popUpTo(nav.graph.startDestinationId) { saveState = true }
                            launchSingleTop = true
                            restoreState = true
                        }
                    },
                    onOpenWords = {
                        nav.navigate(Routes.Words) {
                            popUpTo(nav.graph.startDestinationId) { saveState = true }
                            launchSingleTop = true
                            restoreState = true
                        }
                    },
                )
            }
            composable(Routes.Letters) { LettersScreen() }
            composable(Routes.Words) { WordsScreen() }
        }
    }
}
