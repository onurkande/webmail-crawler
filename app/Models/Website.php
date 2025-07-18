<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Website extends Model
{
    use HasFactory;
    protected $fillable = ['url'];

    public function mails()
    {
        return $this->hasMany(WebsiteMail::class);
    }

    public function phones()
    {
        return $this->hasMany(WebsitePhone::class);
    }
}
