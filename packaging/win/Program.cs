using System.Drawing;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

namespace DevSamosa;

static class Program
{
    const string Url = "https://sanketambilwade.github.io/devsamosa/";

    [STAThread]
    static void Main()
    {
        ApplicationConfiguration.Initialize();

        var form = new Form
        {
            Text = "DevSamosa",
            ClientSize = new Size(1280, 840),
            MinimumSize = new Size(420, 520),
            StartPosition = FormStartPosition.CenterScreen,
            BackColor = ColorTranslator.FromHtml("#0A0A0E"),
        };
        try { form.Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }

        var web = new WebView2 { Dock = DockStyle.Fill, DefaultBackgroundColor = form.BackColor };
        form.Controls.Add(web);

        web.CoreWebView2InitializationCompleted += (_, e) =>
        {
            if (!e.IsSuccess)
            {
                MessageBox.Show(
                    "DevSamosa needs the Microsoft Edge WebView2 runtime, which is missing.\n\n" +
                    "Install it from:\nhttps://developer.microsoft.com/microsoft-edge/webview2/",
                    "DevSamosa", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                Application.Exit();
                return;
            }

            var s = web.CoreWebView2.Settings;
            s.AreDefaultContextMenusEnabled = false;   /* no "view source" right-click */
            s.IsStatusBarEnabled = false;
            s.AreBrowserAcceleratorKeysEnabled = false;

            /* links to GitHub and the token pages should open in the real browser,
               not trap the user inside this window with no address bar */
            web.CoreWebView2.NewWindowRequested += (_, ev) =>
            {
                ev.Handled = true;
                try
                {
                    System.Diagnostics.Process.Start(
                        new System.Diagnostics.ProcessStartInfo(ev.Uri) { UseShellExecute = true });
                }
                catch { }
            };

            web.CoreWebView2.Navigate(Url);
        };

        /* storage lives beside the exe's user data, so the PIN survives restarts */
        var dataDir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "DevSamosa");
        Directory.CreateDirectory(dataDir);
        CoreWebView2Environment.CreateAsync(null, dataDir).ContinueWith(t =>
        {
            form.BeginInvoke(() => web.EnsureCoreWebView2Async(t.Result));
        });

        Application.Run(form);
    }
}
