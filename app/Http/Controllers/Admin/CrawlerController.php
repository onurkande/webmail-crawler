<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;
use App\Models\Website;
use App\Models\WebsiteMail;
use App\Models\WebsitePhone;
use App\Models\WebsiteErrorMail;
use Illuminate\Support\Facades\Log;

class CrawlerController extends Controller
{
    public function create()
    {
        return view('admin.websites.create');
    }

    public function run(Request $request)
    {
        $request->validate([
            'search_query' => 'required|string',
            'links_count' => 'required|integer|min:1|max:1000',
        ]);

        // Python scriptine parametreleri gönder
        $searchQuery = $request->input('search_query');
        $linksCount = $request->input('links_count');

        try {
            // Mevcut url'leri topla ve json dosyasına yaz
            $websiteUrls = Website::pluck('url')->toArray();
            $errorUrls = WebsiteErrorMail::pluck('url')->toArray();
            $dbUrls = array_unique(array_merge($websiteUrls, $errorUrls));
            $existingUrlsPath = base_path('webmail-crawler-python/existing_urls.json');
            
            if (file_exists($existingUrlsPath)) {
                $existingUrls = json_decode(file_get_contents($existingUrlsPath), true) ?? [];
                $newUrls = array_diff($dbUrls, $existingUrls);
                $mergedUrls = array_unique(array_merge($existingUrls, $newUrls));
            } else {
                $mergedUrls = $dbUrls;
            }

            if (!file_put_contents($existingUrlsPath, json_encode($mergedUrls, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT))) {
                Log::error('URL\'ler JSON dosyasına yazılamadı', [
                    'path' => $existingUrlsPath
                ]);
                throw new \Exception('URL\'ler JSON dosyasına yazılamadı');
            }

            $pythonPath = base_path('webmail-crawler-python/venv/Scripts/python.exe');  // Windows için
            $scriptPath = base_path('webmail-crawler-python/crawler.py');

            $process = new Process([$pythonPath, $scriptPath, $searchQuery, $linksCount, $existingUrlsPath]);
            $process->setTimeout(7300); // 2 saat
            $process->run();

            if (!$process->isSuccessful()) {
                Log::error('Python script çalıştırma hatası', [
                    'error' => $process->getErrorOutput(),
                    'command' => $process->getCommandLine()
                ]);
                throw new ProcessFailedException($process);
            }

        } catch (\Exception $e) {
            Log::error('Crawler çalıştırma hatası', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            throw $e;
        }

        // JSON dosyalarını oku
        $outputFile = base_path('webmail-crawler-python/output.json');
        $failedFile = base_path('webmail-crawler-python/failed_output.json');

        $output = json_decode(file_get_contents($outputFile), true);
        $failed = json_decode(file_get_contents($failedFile), true);

        // Başarılı olanları kaydet
        foreach ($output as $entry) {
            // Eğer email veya phone boşsa WebsiteErrorMail tablosuna kaydet
            if (empty($entry['email'])) {
                WebsiteErrorMail::firstOrCreate([
                    'url' => $entry['website'],
                    'email' => $entry['email'],
                    'phone' => $entry['phone']
                ]);
                continue;
            }

            $website = Website::firstOrCreate(['url' => $entry['website']]);

            WebsiteMail::firstOrCreate([
                'website_id' => $website->id,
                'email' => $entry['email']
            ]);

            WebsitePhone::firstOrCreate([
                'website_id' => $website->id,
                'phone' => $entry['phone']
            ]);
        }

        // Başarısız olanları WebsiteErrorMail tablosuna kaydet
        foreach ($failed as $entry) {
            WebsiteErrorMail::firstOrCreate([
                'url' => $entry['website'],
                'email' => $entry['email'] ?? '',
                'phone' => $entry['phone'] ?? ''
            ]);
        }

        return response()->json([
            'message' => 'Tarama tamamlandı!',
            'found' => count($output),
            'not_found' => count($failed),
        ]);
    }
}
