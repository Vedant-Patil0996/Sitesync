'use client';

import React, { useEffect, useState, useRef } from 'react';
import { Languages } from 'lucide-react';
import { Button } from '@/components/ui/button';

const SCRIPT_ID = 'google-translate-script';

const setLanguageCookie = (lang: string) => {
  document.cookie = `googtrans=/en/${lang}; path=/`;
  window.location.reload();
};

const resetLanguageCookie = () => {
  document.cookie = 'googtrans=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
  window.location.reload();
};

export function LanguageSelect() {
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Load Google Translate script robustly
  useEffect(() => {
    if (document.getElementById(SCRIPT_ID)) {
      return;
    }

    // @ts-ignore
    window.googleTranslateElementInit = () => {
      // @ts-ignore
      new window.google.translate.TranslateElement(
        {
          pageLanguage: 'en',
          includedLanguages: 'en,hi,mr,gu',
          // @ts-ignore
          layout: window.google.translate.TranslateElement.InlineLayout.SIMPLE,
          autoDisplay: false,
        },
        'google_translate_element_hidden'
      );
    };

    const script = document.createElement('script');
    script.id = SCRIPT_ID;
    script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
    script.async = true;
    document.body.appendChild(script);

    return () => {
      // We don't remove the script to avoid reloading issues
    };
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownRef]);

  const handleLanguageChange = (lang: string) => {
    if (lang === 'en') {
      resetLanguageCookie();
    } else {
      setLanguageCookie(lang);
    }
    setShowDropdown(false);
  };

  return (
    <div style={{ position: 'relative' }} ref={dropdownRef}>
      {/* Custom Toggle Button */}
      <Button
        id="translateToggle"
        variant="outline"
        size="icon"
        onClick={() => setShowDropdown((prev) => !prev)}
        aria-label="Translate"
      >
        <Languages className="h-5 w-5" />
      </Button>

      {/* Our Custom Dropdown */}
      {showDropdown && (
        <div
          className="custom-translate-dropdown border-2 border-border bg-card shadow-brutal-sm absolute top-[calc(100%+8px)] right-0 z-[1001] overflow-hidden min-w-[120px]"
        >
          <button
            className="block w-full text-left px-4 py-2 font-medium text-sm hover:bg-accent hover:text-accent-foreground"
            onClick={() => handleLanguageChange('en')}
          >
            English
          </button>
          <button
            className="block w-full text-left px-4 py-2 font-medium text-sm hover:bg-accent hover:text-accent-foreground"
            onClick={() => handleLanguageChange('hi')}
          >
            हिंदी
          </button>
          <button
            className="block w-full text-left px-4 py-2 font-medium text-sm hover:bg-accent hover:text-accent-foreground"
            onClick={() => handleLanguageChange('mr')}
          >
            मराठी
          </button>
          <button
            className="block w-full text-left px-4 py-2 font-medium text-sm hover:bg-accent hover:text-accent-foreground"
            onClick={() => handleLanguageChange('gu')}
          >
            ગુજરાતી
          </button>
        </div>
      )}

      {/* Hidden div to hold the *actual* Google widget */}
      <div id="google_translate_element_hidden" style={{ display: 'none' }}></div>

      {/* Styles for the *widget* and *our dropdown* ONLY */}
      <style>{`
        /* Hide the default Google widget and all its parts */
        #google_translate_element_hidden,
        .goog-te-gadget,
        .goog-te-combo,
        .goog-te-combo select,
        .goog-te-combo .goog-te-menu-value {
          display: none !important;
          visibility: hidden !important;
        }

        /* Hide specific Google elements if they appear */
        .VIpgJd-ZVi9od-ORHb-OEVmCD, /* The Google logo container */
        .VIpgJd-ZVi9od-ORHb-OEVmCD img { /* The Google logo itself */
            display: none !important;
            visibility: hidden !important;
        }
        
        /* Force body top to 0 to prevent Google Translate jump */
        body {
            top: 0 !important;
        }
      `}</style>
    </div>
  );
}
