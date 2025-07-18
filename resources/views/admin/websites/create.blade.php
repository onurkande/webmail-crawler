@extends('admin.layouts.master')

@section('title', 'Web Crawler Başlat')
@section('content')
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header bg-primary text-white">Web Crawler Başlat</div>
            <div class="card-body">
                @if(session('message'))
                    <div class="alert alert-success">{{ session('message') }}</div>
                @endif
                @if($errors->any())
                    <div class="alert alert-danger">
                        <ul class="mb-0">
                            @foreach($errors->all() as $error)
                                <li>{{ $error }}</li>
                            @endforeach
                        </ul>
                    </div>
                @endif
                <form method="POST" action="{{ route('admin.crawler.run') }}">
                    @csrf
                    <div class="form-group mb-3">
                        <label for="search_query">Arama Sorgusu</label>
                        <input type="text" class="form-control" id="search_query" name="search_query" value="{{ old('search_query', 'software agentur site:de') }}" required placeholder="Örn: software agentur site:de">
                    </div>
                    <div class="form-group mb-3">
                        <label for="links_count">Link Sayısı</label>
                        <input type="number" class="form-control" id="links_count" name="links_count" value="{{ old('links_count', 100) }}" min="1" max="1000" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Taramayı Başlat</button>
                </form>
            </div>
        </div>
    </div>
</div>
@endsection

@section('scripts')

@endsection
