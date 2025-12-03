/**
 * Tests for VPN Component
 */

// Mock dependencies before importing
jest.mock('../../js/utils/dom.js', () => ({
    escapeHtml: jest.fn(text => text || ''),
    icon: jest.fn(name => `<i data-lucide="${name}"></i>`),
    refreshIcons: jest.fn(),
    setButtonLoading: jest.fn()
}));

jest.mock('../../js/i18n.js', () => ({
    t: jest.fn(key => key)
}));

jest.mock('../../js/utils/toast.js', () => ({
    showToast: jest.fn()
}));

import { renderVPNStatus, renderVPNProfiles, activateProfile, deleteProfile, loadVPNSettings, initVPNEvents } from '../../js/components/vpn.js';
import { escapeHtml, icon, refreshIcons, setButtonLoading } from '../../js/utils/dom.js';
import { t } from '../../js/i18n.js';
import { showToast } from '../../js/utils/toast.js';

describe('VPN Component', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="vpn-status-detail"></div>
            <div id="vpn-profiles"></div>
            <input id="vpn-ping-host" />
            <input id="vpn-check-interval" />
        `;
        jest.clearAllMocks();
        global.confirm = jest.fn();
    });

    describe('renderVPNStatus', () => {
        it('should render inactive status when VPN is not active', () => {
            const data = { active: false };

            renderVPNStatus(data);

            const container = document.getElementById('vpn-status-detail');
            expect(t).toHaveBeenCalledWith('vpn_inactive');
            expect(t).toHaveBeenCalledWith('import_profile_hint');
            expect(container.innerHTML).toContain('bg-red-500');
        });

        it('should render active status when VPN is active', () => {
            const data = {
                active: true,
                endpoint: '192.168.1.1:51820',
                latest_handshake: '2 minutes ago',
                transfer: { received: '1.5 GB', sent: '500 MB' }
            };

            renderVPNStatus(data);

            expect(t).toHaveBeenCalledWith('vpn_active');
            const container = document.getElementById('vpn-status-detail');
            expect(container.innerHTML).toContain('bg-green-500');
        });

        it('should escape endpoint data', () => {
            const data = {
                active: true,
                endpoint: '<script>evil</script>',
                transfer: { received: '0 B', sent: '0 B' }
            };

            renderVPNStatus(data);

            expect(escapeHtml).toHaveBeenCalledWith('<script>evil</script>');
        });

        it('should display transfer statistics', () => {
            const data = {
                active: true,
                transfer: { received: '1.5 GB', sent: '500 MB' }
            };

            renderVPNStatus(data);

            expect(escapeHtml).toHaveBeenCalledWith('1.5 GB');
            expect(escapeHtml).toHaveBeenCalledWith('500 MB');
            expect(t).toHaveBeenCalledWith('transfer');
        });

        it('should display endpoint when available', () => {
            const data = {
                active: true,
                endpoint: 'vpn.example.com:51820',
                transfer: { received: '0 B', sent: '0 B' }
            };

            renderVPNStatus(data);

            expect(escapeHtml).toHaveBeenCalledWith('vpn.example.com:51820');
            expect(t).toHaveBeenCalledWith('endpoint');
        });

        it('should display last handshake when available', () => {
            const data = {
                active: true,
                latest_handshake: '5 minutes ago',
                transfer: { received: '0 B', sent: '0 B' }
            };

            renderVPNStatus(data);

            expect(escapeHtml).toHaveBeenCalledWith('5 minutes ago');
            expect(t).toHaveBeenCalledWith('last_handshake');
        });

        it('should handle missing container gracefully', () => {
            document.body.innerHTML = '';

            expect(() => renderVPNStatus({ active: true })).not.toThrow();
        });

        it('should handle missing transfer data', () => {
            const data = { active: true };

            renderVPNStatus(data);

            const container = document.getElementById('vpn-status-detail');
            expect(container.innerHTML).toContain('0 B');
        });
    });

    describe('renderVPNProfiles', () => {
        it('should render list of profiles', () => {
            const profiles = [
                { name: 'Profile1', active: false },
                { name: 'Profile2', active: true }
            ];

            renderVPNProfiles(profiles);

            const container = document.getElementById('vpn-profiles');
            expect(container.children.length).toBe(2);
        });

        it('should show no profiles message when empty', () => {
            renderVPNProfiles([]);

            expect(t).toHaveBeenCalledWith('no_profiles');
        });

        it('should show no profiles message when null', () => {
            renderVPNProfiles(null);

            expect(t).toHaveBeenCalledWith('no_profiles');
        });

        it('should escape profile names', () => {
            const profiles = [
                { name: '<script>evil</script>', active: false }
            ];

            renderVPNProfiles(profiles);

            expect(escapeHtml).toHaveBeenCalledWith('<script>evil</script>');
        });

        it('should escape profile names in data attributes', () => {
            const profiles = [
                { name: "Profile'With'Quotes", active: false }
            ];

            renderVPNProfiles(profiles);

            // Profile name is escaped via escapeHtml for data attributes
            expect(escapeHtml).toHaveBeenCalledWith("Profile'With'Quotes");
        });

        it('should show activate and delete buttons with data attributes for inactive profiles', () => {
            const profiles = [
                { name: 'InactiveProfile', active: false }
            ];

            renderVPNProfiles(profiles);

            const container = document.getElementById('vpn-profiles');
            expect(container.innerHTML).toContain('data-action="activate-vpn"');
            expect(container.innerHTML).toContain('data-action="delete-vpn"');
            expect(container.innerHTML).toContain('data-name="InactiveProfile"');
            expect(t).toHaveBeenCalledWith('activate');
            expect(t).toHaveBeenCalledWith('delete');
        });

        it('should show active label for active profile', () => {
            const profiles = [
                { name: 'ActiveProfile', active: true }
            ];

            renderVPNProfiles(profiles);

            expect(t).toHaveBeenCalledWith('active');
            const container = document.getElementById('vpn-profiles');
            expect(container.innerHTML).not.toContain('data-action="activate-vpn"');
            expect(container.innerHTML).not.toContain('data-action="delete-vpn"');
        });

        it('should call refreshIcons after rendering', () => {
            const profiles = [{ name: 'Test', active: false }];

            renderVPNProfiles(profiles);

            expect(refreshIcons).toHaveBeenCalled();
        });

        it('should show green indicator for active profile', () => {
            const profiles = [
                { name: 'Active', active: true }
            ];

            renderVPNProfiles(profiles);

            const container = document.getElementById('vpn-profiles');
            expect(container.innerHTML).toContain('bg-green-500');
        });

        it('should show gray indicator for inactive profile', () => {
            const profiles = [
                { name: 'Inactive', active: false }
            ];

            renderVPNProfiles(profiles);

            const container = document.getElementById('vpn-profiles');
            expect(container.innerHTML).toContain('bg-gray-500');
        });

        it('should handle missing container gracefully', () => {
            document.body.innerHTML = '';

            expect(() => renderVPNProfiles([{ name: 'Test', active: false }]))
                .not.toThrow();
        });
    });

    describe('activateProfile', () => {
        let button;

        beforeEach(() => {
            button = document.createElement('button');
            document.body.appendChild(button);
        });

        it('should set button loading state', () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            activateProfile('TestProfile', button);

            expect(setButtonLoading).toHaveBeenCalledWith(button, true);
        });

        it('should call API with correct payload', () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            activateProfile('MyProfile', button);

            expect(global.fetch).toHaveBeenCalledWith('/api/vpn/activate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: 'MyProfile' })
            });
        });

        it('should show success toast on activation', async () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            await activateProfile('TestProfile', button);
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(showToast).toHaveBeenCalledWith(
                expect.stringContaining('TestProfile'),
                'success'
            );
        });

        it('should show error toast on failure', async () => {
            global.fetch.mockResolvedValue({
                ok: false,
                json: () => Promise.resolve({ detail: 'Activation failed' })
            });

            await activateProfile('TestProfile', button);
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(showToast).toHaveBeenCalledWith('Activation failed', 'error');
        });

        it('should reset button loading state after completion', async () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            await activateProfile('TestProfile', button);
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(setButtonLoading).toHaveBeenCalledWith(button, false);
        });

        it('should trigger htmx reload on success', async () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            await activateProfile('TestProfile', button);
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(global.htmx.trigger).toHaveBeenCalledWith('#vpn-profiles', 'htmx:load');
            expect(global.htmx.trigger).toHaveBeenCalledWith('#vpn-status-detail', 'htmx:load');
        });
    });

    describe('deleteProfile', () => {
        let button;

        beforeEach(() => {
            button = document.createElement('button');
            document.body.appendChild(button);
        });

        it('should ask for confirmation', () => {
            global.confirm.mockReturnValue(true);
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            deleteProfile('TestProfile', button);

            expect(global.confirm).toHaveBeenCalledWith(expect.stringContaining('TestProfile'));
        });

        it('should not proceed if not confirmed', () => {
            global.confirm.mockReturnValue(false);

            deleteProfile('TestProfile', button);

            expect(global.fetch).not.toHaveBeenCalled();
        });

        it('should call delete API with correct URL', () => {
            global.confirm.mockReturnValue(true);
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            deleteProfile('MyProfile', button);

            expect(global.fetch).toHaveBeenCalledWith(
                '/api/vpn/profiles/MyProfile',
                { method: 'DELETE' }
            );
        });

        it('should encode profile name in URL', () => {
            global.confirm.mockReturnValue(true);
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            deleteProfile('Profile With Spaces', button);

            expect(global.fetch).toHaveBeenCalledWith(
                '/api/vpn/profiles/Profile%20With%20Spaces',
                { method: 'DELETE' }
            );
        });

        it('should show success toast on deletion', async () => {
            global.confirm.mockReturnValue(true);
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            await deleteProfile('TestProfile', button);
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(showToast).toHaveBeenCalledWith(
                expect.stringContaining('TestProfile'),
                'success'
            );
        });

        it('should show error toast on failure', async () => {
            global.confirm.mockReturnValue(true);
            global.fetch.mockResolvedValue({
                ok: false,
                json: () => Promise.resolve({ detail: 'Cannot delete active profile' })
            });

            await deleteProfile('TestProfile', button);
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(showToast).toHaveBeenCalledWith('Cannot delete active profile', 'error');
        });

        it('should trigger htmx reload on success', async () => {
            global.confirm.mockReturnValue(true);
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            await deleteProfile('TestProfile', button);
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(global.htmx.trigger).toHaveBeenCalledWith('#vpn-profiles', 'htmx:load');
        });
    });

    describe('loadVPNSettings', () => {
        it('should load settings from API', async () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ ping_host: '1.1.1.1', check_interval: 90 })
            });

            await loadVPNSettings();

            expect(global.fetch).toHaveBeenCalledWith('/api/settings/vpn');
        });

        it('should populate form fields with API data', async () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ ping_host: '1.1.1.1', check_interval: 90 })
            });

            await loadVPNSettings();

            expect(document.getElementById('vpn-ping-host').value).toBe('1.1.1.1');
            expect(document.getElementById('vpn-check-interval').value).toBe('90');
        });

        it('should use default values when API returns empty', async () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            await loadVPNSettings();

            expect(document.getElementById('vpn-ping-host').value).toBe('8.8.8.8');
            expect(document.getElementById('vpn-check-interval').value).toBe('60');
        });

        it('should handle API errors gracefully', async () => {
            global.fetch.mockRejectedValue(new Error('Network error'));

            await expect(loadVPNSettings()).resolves.not.toThrow();
        });

        it('should handle missing form fields gracefully', async () => {
            document.body.innerHTML = '';
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ ping_host: '1.1.1.1' })
            });

            await expect(loadVPNSettings()).resolves.not.toThrow();
        });
    });

    describe('initVPNEvents', () => {
        it('should be a function for setting up event delegation', () => {
            expect(typeof initVPNEvents).toBe('function');
        });

        it('should not throw when called', () => {
            expect(() => initVPNEvents()).not.toThrow();
        });

        it('should handle activate-vpn action when clicked', () => {
            initVPNEvents();
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            document.body.innerHTML = `
                <button data-action="activate-vpn" data-name="TestProfile">Activate</button>
            `;

            const button = document.querySelector('[data-action="activate-vpn"]');
            button.click();

            expect(global.fetch).toHaveBeenCalledWith('/api/vpn/activate', expect.objectContaining({
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: 'TestProfile' })
            }));
        });

        it('should handle delete-vpn action when clicked', () => {
            initVPNEvents();
            global.confirm.mockReturnValue(true);
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({})
            });

            document.body.innerHTML = `
                <button data-action="delete-vpn" data-name="TestProfile">Delete</button>
            `;

            const button = document.querySelector('[data-action="delete-vpn"]');
            button.click();

            expect(global.confirm).toHaveBeenCalled();
            expect(global.fetch).toHaveBeenCalledWith('/api/vpn/profiles/TestProfile', expect.objectContaining({ method: 'DELETE' }));
        });

        it('should ignore clicks on elements without data-action', () => {
            initVPNEvents();

            document.body.innerHTML = `<button>Regular Button</button>`;
            const button = document.querySelector('button');

            expect(() => button.click()).not.toThrow();
            expect(global.fetch).not.toHaveBeenCalled();
        });

        it('should ignore activate-vpn without name', () => {
            initVPNEvents();

            document.body.innerHTML = `
                <button data-action="activate-vpn">Activate</button>
            `;

            const button = document.querySelector('[data-action="activate-vpn"]');
            button.click();

            expect(global.fetch).not.toHaveBeenCalled();
        });

        it('should ignore delete-vpn without name', () => {
            initVPNEvents();

            document.body.innerHTML = `
                <button data-action="delete-vpn">Delete</button>
            `;

            const button = document.querySelector('[data-action="delete-vpn"]');
            button.click();

            expect(global.fetch).not.toHaveBeenCalled();
        });
    });

    describe('loadVPNSettings additional tests', () => {
        it('should handle non-ok response', async () => {
            global.fetch.mockResolvedValue({
                ok: false,
                json: () => Promise.resolve({})
            });

            await expect(loadVPNSettings()).resolves.not.toThrow();
        });
    });
});
