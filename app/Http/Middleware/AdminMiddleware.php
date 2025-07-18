<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class AdminMiddleware
{
    public function handle(Request $request, Closure $next): Response
    {
        if (!auth()->check() || auth()->user()->isAdmin !== 'admin') {
            return redirect('/')->with('error', 'Bu sayfaya erişim yetkiniz bulunmamaktadır.');
        }

        return $next($request);
    }
} 