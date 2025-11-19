# SharePoint Embedding Guide

## What Was Changed

The application has been configured to allow embedding in SharePoint iframes with the following changes:

1. **CORS Support**: Added Flask-CORS to handle cross-origin requests from SharePoint
2. **Security Headers**: 
   - `X-Frame-Options`: Allows framing from SharePoint domains
   - `Content-Security-Policy`: Specifies allowed frame ancestors
   - `Access-Control-Allow-Credentials`: Enables credential sharing

## How to Embed in SharePoint

### Method 1: Embed Web Part (Recommended)

1. Edit your SharePoint page
2. Click **+ (Add section/web part)**
3. Search for **"Embed"** web part
4. Add the Embed web part to your page
5. In the Embed code field, paste:
   ```html
   <iframe 
     src="https://svarc.100pctwifi.nl/arcrooms/" 
     width="100%" 
     height="800px" 
     frameborder="0"
     style="border: none; overflow: hidden;">
   </iframe>
   ```
6. Click **Apply**
7. Publish the page

### Method 2: Script Editor Web Part (Classic Pages)

If using classic SharePoint pages:

1. Edit the page
2. Insert → Web Part → Script Editor
3. Click "Edit Snippet"
4. Paste the iframe code above
5. Save

### Method 3: Full-Width Embedding

For a full-width experience:

```html
<iframe 
  src="https://svarc.100pctwifi.nl/arcrooms/" 
  width="100%" 
  height="100vh" 
  frameborder="0"
  style="border: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;">
</iframe>
```

## Authentication Considerations

**Important**: Users will need to authenticate when they first access the embedded app. They'll see the Microsoft login within the iframe.

### Improving User Experience

To avoid double-authentication (SharePoint + your app):

1. **Option A**: Pre-authenticate users by linking to `/arcrooms/` before embedding
2. **Option B**: Use SharePoint's user context (requires SPFx - more complex)

## Allowed Domains

The app is configured to accept requests from:
- `https://svarc.sharepoint.com`
- `https://*.sharepoint.com` (any SharePoint subdomain)
- `https://svarc.100pctwifi.nl` (your main site)

### Adding More Domains

Edit `/home/martijn/arcRooms/app.py` around line 17:

```python
"origins": [
    "https://svarc.sharepoint.com",
    "https://*.sharepoint.com",
    "https://your-new-domain.com"  # Add here
],
```

Then restart: `sudo systemctl restart arcrooms`

## Troubleshooting

### Issue: "Refused to display in a frame"

**Solution**: Check browser console for CSP errors. Verify the SharePoint URL matches the allowed origins.

### Issue: Authentication loop

**Solution**: Ensure cookies are allowed for third-party sites in browser settings. Some browsers block this by default.

### Issue: Page not loading

**Solution**: 
1. Check if app is running: `sudo systemctl status arcrooms`
2. Verify CORS headers: `curl -H "Origin: https://svarc.sharepoint.com" https://svarc.100pctwifi.nl/arcrooms/`

## Mobile Considerations

The embedded iframe works on mobile SharePoint apps, but consider:
- Touch gestures may conflict with SharePoint's native gestures
- Smaller screen = more scrolling within the iframe
- Test on actual devices before deploying

## Performance Tips

1. **Set appropriate height**: Use `height="800px"` or adjust based on content
2. **Lazy loading**: Add `loading="lazy"` to iframe for better page performance
3. **Cache headers**: Already configured for static assets

## Security Notes

- The app uses session cookies with `SameSite=None` for cross-origin support
- Authentication is handled by Microsoft OAuth 2.0
- All data transmission is over HTTPS
- Frame ancestors are restricted to known SharePoint domains

## Testing

Before deploying to production SharePoint:

1. Test in SharePoint test/dev site first
2. Check different browsers (Edge, Chrome, Firefox)
3. Verify mobile experience
4. Test authentication flow with different user roles

## Next Steps (Optional Enhancements)

1. **Single Sign-On**: Implement token passing from SharePoint context
2. **Deep Linking**: Add URL parameters for specific rooms/dates
3. **Responsive Heights**: Use postMessage API to auto-adjust iframe height
4. **SharePoint Theme**: Match SharePoint's color scheme dynamically
