<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class WebsiteMail extends Model
{
    use HasFactory;
    protected $fillable = ['website_id', 'email'];

    public function website()
    {
        return $this->belongsTo(Website::class, 'website_id');
    }
}
