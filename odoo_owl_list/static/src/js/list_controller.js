// /** @odoo-module */

// import { ListController } from "@web/views/list/list_controller";
// import { registry } from '@web/core/registry';
// import { listView } from '@web/views/list/list_view';

// export class OdooOWLListController extends ListController {
//     setup() {
//        super.setup();
//    }
//     openExpirationReminder() {
//         this.actionService.doAction("mm_property_inherit_new.action_tenancy_expiration_reminder");
//     }
// }


// const viewRegistry = registry.category("views");
// export const OWLListController = {
//     ...listView,
//     Controller: OdooOWLListController,
// };
// viewRegistry.add("owl_list_controller", OWLListController);

/** @odoo-module */

// import { ListController } from "@web/views/list/list_controller";
// import { registry } from '@web/core/registry';
// import { listView } from '@web/views/list/list_view';
// import { useState } from "@odoo/owl";

// export class OdooOWLListController extends ListController {
//     setup() {
//         super.setup();
//         this.state = useState({
//             showReminderButton: true
//         });
//     }
    
//     openExpirationReminder() {
//         this.state.showReminderButton = false;
//         this.actionService.doAction("mm_property_inherit_new.action_tenancy_expiration_reminder");
//     }
// }

// const viewRegistry = registry.category("views");
// export const OWLListController = {
//     ...listView,
//     Controller: OdooOWLListController,
// };
// viewRegistry.add("owl_list_controller", OWLListController);


import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { useState } from "@odoo/owl";

export class OdooOWLListController extends ListController {
    setup() {
        super.setup();
        this.customState = useState({
            showReminderButton: true
        });
    }
    
    openExpirationReminder() {
        this.customState.showReminderButton = false;
        this.actionService.doAction("mm_property_inherit_new.action_tenancy_expiration_reminder");
    }
    
    get showReminderButton() {
        return this.customState.showReminderButton;
    }
}

const viewRegistry = registry.category("views");
export const OWLListController = {
    ...listView,
    Controller: OdooOWLListController,
};
viewRegistry.add("owl_list_controller", OWLListController);