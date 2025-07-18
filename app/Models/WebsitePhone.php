<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class WebsitePhone extends Model
{
    use HasFactory;
    protected $fillable = ['website_id', 'phone'];

    public function website()
    {
        return $this->belongsTo(Website::class, 'website_id');
    }
}
