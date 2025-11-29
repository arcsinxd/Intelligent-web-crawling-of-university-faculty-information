package com.example.teachersystemapp; // ⚠️保持这行不变，用您原本的包名

import androidx.appcompat.app.AppCompatActivity;

import android.annotation.SuppressLint;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
// 👇 新增了这个导入，用于处理返回键
import androidx.activity.OnBackPressedCallback;

public class MainActivity extends AppCompatActivity {

    private WebView myWebView;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // 1. 初始化 WebView
        myWebView = findViewById(R.id.webview);
        WebSettings webSettings = myWebView.getSettings();
        webSettings.setJavaScriptEnabled(true);

        // [旧] 这一行是防止跳转到 Chrome 浏览器
        myWebView.setWebViewClient(new WebViewClient());

        // ✅ [新] 添加这一行！这是为了允许 Alert 和 Confirm 弹窗！
        // WebChromeClient 负责处理 JS 的对话框、网站图标、标题等
        myWebView.setWebChromeClient(new android.webkit.WebChromeClient());

        // 加载您的网址 (保持您之前改好的 IP 不变)
        // 如果您之前改成了 192.168.x.x，请继续用那个，不要改回 10.0.2.2
        myWebView.loadUrl("http://192.168.43.46:5000");

        // ... (下面的返回键逻辑保持不变)
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                if (myWebView.canGoBack()) {
                    myWebView.goBack();
                } else {
                    setEnabled(false);
                    getOnBackPressedDispatcher().onBackPressed();
                }
            }
        });
    }

    // ❌ 以前的 public void onBackPressed() 方法彻底删掉，不需要了。
}